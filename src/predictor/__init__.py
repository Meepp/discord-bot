import glob
import os
import queue
import threading
import time

import joblib as joblib
import numpy as np
import pandas
from pandas.api.indexers import BaseIndexer
from sklearn import preprocessing
from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import train_test_split

TEAM_COLUMNS = ["date", "actual_result", "playerid", "gameid", "team", "gamelength", "result", "dragons", "barons",
                "riftheralds", "towers"]
PLAYER_COLUMNS = ["date", "player", "gameid", "kills", "deaths", "assists", "dpm", "damageshare",
                  "damagetakenperminute", "wpm",
                  "vspm", "earned gpm", "cspm", "csat10", "goldat10", "killsat10", "deathsat10", "assistsat10",
                  "csat15", "goldat15", "killsat15", "deathsat15", "assistsat15"]
PATH_TO_DOWNLOAD = os.path.join(os.path.dirname(os.path.realpath(__file__)), "storage\data")


class CustomIndexer(BaseIndexer):
    def get_window_bounds(self, num_values=0, min_periods=None, center=None, closed=None):
        end = np.arange(0, num_values, dtype="int64")
        end += 4
        start = end - 3

        end = np.clip(end, 0, num_values)
        start = np.clip(start, 0, num_values)

        return start, end


def concat_rows(df, n):
    new_cols = [
        f"{col}{idx}"
        for idx in range(1, n + 1)
        for col in df.columns
    ]
    n_cols = len(df.columns)
    new_df = pandas.DataFrame(
        df.values.reshape([-1, n_cols * n]),
        columns=new_cols
    )
    return new_df


def get_team(data, team_name):
    teams = data.team.unique().astype(str).flatten()
    if team_name in teams:
        return team_name
    matches = np.char.find(teams, team_name)
    selection = teams[matches >= 0]
    if len(selection) == 0:
        print("No teams found with that name.")
        return None
    if len(selection) > 1:
        print("Multiple teams found: %s" % ", ".join(selection))
        return None
    return selection[0]


def prepare_predict_data(all_data, blue_team="Fnatic", red_team="Rogue"):
    blue_team = get_team(all_data, blue_team)
    red_team = get_team(all_data, red_team)
    if blue_team is None or red_team is None:
        return

    aggregation = None
    for team in [blue_team, red_team]:
        players = all_data.query(f"team=='{team}'").filter(["player"]).head(5)

        for player in players.player.values:
            new_player_data = (
                all_data
                    .filter(PLAYER_COLUMNS)
                    .query(f"player == '{player}'")
                    .head(3)
                    .mean(axis=0)
                    .to_frame()
                    .transpose()
            )

            if aggregation is None:
                aggregation = new_player_data
            else:
                aggregation = aggregation.append(new_player_data, ignore_index=True)

    aggregation = aggregation.reindex(sorted(aggregation.columns), axis=1)
    aggregation = concat_rows(aggregation, 10)
    blue_team_data = (
        all_data
            .query("playerid > 10")
            .query(f"team=='{blue_team}'")
            .filter(TEAM_COLUMNS)
            .head(3)
            .rolling(3, on="actual_result")
            .mean()
            .tail(1)
    )
    red_team_data = (
        all_data
            .query("playerid > 10")
            .query(f"team=='{red_team}'")
            .filter(TEAM_COLUMNS)
            .head(3)
            .rolling(3, on="actual_result")
            .mean()
            .tail(1)
    )
    assert(len(red_team_data) > 0)
    assert(len(blue_team_data) > 0)
    new_team_data = blue_team_data.append(red_team_data, ignore_index=True)
    new_team_data = concat_rows(new_team_data, 2)

    new_team_data.drop(columns=["actual_result2", "playerid1", "playerid2"], inplace=True)

    new_game_data = (
        pandas
            .concat([new_team_data, aggregation], axis=1)
            .fillna(0)
    )

    new_game_data.drop(columns=["actual_result1"], inplace=True)

    return new_game_data


def get_all_data(path):
    all_files = glob.glob(path + "/*.csv")
    li = []

    for filename in all_files:
        df = pandas.read_csv(filename, index_col=None, header=0)
        li.append(df)

    data = pandas.concat(li, axis=0, ignore_index=True)

    data = data.sort_values(by=["date", "playerid"], ascending=[0, 1])
    data = data.reset_index(drop=True)
    data["actual_result"] = data["result"]

    return data


def prepare_data(data):
    indexer = CustomIndexer(window_size=1)

    player_data = (
        data
            .filter(PLAYER_COLUMNS)
            .groupby(pandas.Grouper(key="player"))
            .rolling(window=indexer, min_periods=1, on="gameid")
            .mean()
            .reset_index()
            .rename(columns={"level_1": "id"})
            .sort_values(by="id")
            .reset_index()
            .drop(columns=["index", "player", "id", "gameid"])
    )

    team_data = (
        data
            .query("playerid > 10")
            .filter(TEAM_COLUMNS)
            .groupby(pandas.Grouper(key="team"))
            .rolling(window=indexer, min_periods=1, on="actual_result")
            .mean()
            .reset_index()
            .rename(columns={"level_1": "id"})
            .sort_values(by="id")
            .reset_index()
            .drop(columns=["index", "playerid", "id"])
    )

    game_data_player = concat_rows(player_data, 10)
    game_data_team = concat_rows(team_data, 2)
    game_data_team.drop(columns=["actual_result2", "team1", "team2"], inplace=True)

    game_data = (
        pandas
            .concat([game_data_team, game_data_player], axis=1)
            .dropna()
    )

    game_result = game_data["actual_result1"]
    game_data.drop(columns=["actual_result1"], inplace=True)
    return game_data, game_result


def fit_model(x, y):
    lab_enc = preprocessing.LabelEncoder()
    encoded = lab_enc.fit_transform(y)

    trainX, testX, trainY, testY = train_test_split(
        x, encoded, test_size=.33)
    model = RidgeClassifier()
    model.fit(trainX, trainY)

    print(model.score(trainX, trainY))
    print(model.score(testX, testY))

    return model


def fetch_data():
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    # Setup firefox preferences
    profile = webdriver.FirefoxProfile()

    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "binary/octet-stream,text/csv")
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", PATH_TO_DOWNLOAD)

    # Setup a headless firefox client
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(profile, options=options)

    # Fetch url
    driver.get("https://oracleselixir.com/tools/downloads")

    time.sleep(2)
    elements = driver.find_elements_by_tag_name("a")
    for element in elements:
        if "2021 Match Data" in element.text:
            url = element.get_attribute("href")
            driver.get(url)
            driver.close()


class Predictor:
    def __init__(self):
        # TODO: Only do this once every week or so
        update_data = False

        self.model = None

        # Update CSVs by fetching them from server.
        if update_data:
            print("Fetching new data from OraclesElixir")
            fetch_data()
        # If not updating the data, attempt to fetch a model from disk.
        else:
            try:
                self.model = joblib.load("storage/models/model0.2.joblib")
            except FileNotFoundError as e:
                print("[Predictor] No model found on disk (storage/models), creating a new model.")
            print("[Predictor] Fetched model from disk.")

        print("[Predictor] Creating dataframe from CSVs.")
        self.data = get_all_data("storage/data")

        # Update prediction model with new data
        if self.model is None:
            print("[Predictor] Preparing data.")
            game_data, game_result = prepare_data(self.data)
            print("[Predictor] Fitting model.")
            self.model = fit_model(game_data, game_result)

            # Store model to disk.
            joblib.dump(self.model, "storage/models/model0.2.joblib")

    def synchronized_compute_prediction(self, blue, red):
        predict_data = prepare_predict_data(self.data, blue, red)
        if predict_data is not None:
            prob = (self.model.decision_function(predict_data)[0] + 1) / 2
            
            if not (0 < prob < 1):
                # Backup if the probability is fucked
                import random
                random.seed(blue+red)
                prob = random.random()
            odds = (1 / prob, 1 / (1 - prob))
            return odds