from discord import User
from pymongo import ReturnDocument

from database import mongodb as db
from database.models.models import Profile


def get_money(user: User):
    result = db['profile'].find_one({"owner_id": user.id})
    # TODO check if this works
    if not result:
        # TODO add init money back
        profile_of_user = Profile(user)
        profile_of_user.init_balance()
        result = db['profile'].insert_one(profile_of_user.to_mongodb())

    return result


def update_money(user: dict, money_update):
    return db['profile'].find_one_and_update(filter={"_id": user['_id']}, update={"$inc": {'balance': money_update}},
                                             upsert=True, return_document=ReturnDocument.AFTER)


def get_profile(user: User = None, user_id: int = None, username: str = None):
    if user is not None:
        return db['profile'].find_one({"owner_id": user.id})
    if user_id is not None:
        return db['profile'].find_one({"owner_id": user_id})
    if username is not None:
        return db['profile'].find_one({"owner": username})


def update_active_playlist(profile: dict, value):
    return db['profile'].find_one_and_update(filter={"_id": profile['_id']}, update={"$set": {"active_playlist": value}},
                                             upsert=True, return_document=ReturnDocument.AFTER)