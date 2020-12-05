from discord import User

from database import db
from database.models.models import Profile
from database.repository import honor_repository


def get_money(user: User):
    session = db.session()

    result = session.query(Profile).filter(Profile.owner_id == user.id).one_or_none()

    if not result:
        result = Profile(user)
        result.init_balance(session, user)
        session.add(result)
        session.commit()
    return result


def get_profile(user: User):
    session = db.session()
    return session.query(Profile).filter(Profile.owner_id == user.id).one_or_none()
