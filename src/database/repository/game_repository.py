from discord import User

from database import db
from database.models.models import LeagueGame


def get_games(user: User, game_id: str):
    session = db.session()

    return session.query(LeagueGame).filter(LeagueGame.game_id == game_id, LeagueGame.owner_id == user.id).all()

def remove_game(db_id):
    session = db.session()
    session.query(LeagueGame).filter(LeagueGame.id==db_id).delete()
    session.commit()
    return "Deleted %d" % db_id