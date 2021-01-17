from discord import User

from database import db
from database.models.models import Profile
from database.repository import honor_repository


def get_money(user: User):
    session = db.session()

    result = session.query(Profile).filter(Profile.discord_id == user.id).one_or_none()

    if not result:
        result = Profile(user)
        result.init_balance(session, user)
        session.add(result)
        session.commit()
    return result


def get_profile(user: User = None, user_id: int = None):
    session = db.session()

    sub = session.query(Profile)
    if user is not None:
        return sub.filter(Profile.discord_id == user.id).one_or_none()
    if user_id is not None:
        return sub.filter(Profile.discord_id == user_id).one_or_none()
