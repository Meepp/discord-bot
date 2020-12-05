from discord import User

from database import db
from database.models.models import Game


def get_games(user: User, game_id: str):
    session = db.session()

    return session.query(Game).filter(Game.game_id == game_id, Game.owner_id == user.id).all()
