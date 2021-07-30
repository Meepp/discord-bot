from database import mongodb as db


def get_match_by_id(match_id):
    collection = db['esportGame']

    return list(collection.find({"game_id": int(match_id)}))
