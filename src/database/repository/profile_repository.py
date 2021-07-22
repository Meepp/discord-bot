from discord import User
from pymongo import ReturnDocument

from database import mongodb as db
from database.models.models import Profile



def get_money(user: User):
    result = db['profile'].find_one({"owner_id": user.id})
    # TODO check if this works
    if not result:
        # TODO add init money back
        db['profile'].insert_one(Profile(user).to_mongodb())

    return result


def add_money(user: User, money_to_add):
    return db['profile'].find_one_and_update(filter={"owner_id": user.id}, update={"$inc": {'balance': money_to_add}},
                                         upsert=True, return_document=ReturnDocument.AFTER)


def get_profile(user: User = None, user_id: int = None, username: str = None):
    if user is not None:
        return db['profile'].find({"owner_id": user.id})
    if user_id is not None:
        return db['profile'].find({"owner_id": user_id})
    if username is not None:
        return db['profile'].find({"owner": username})
