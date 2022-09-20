import logging
from functools import wraps
from time import time

from discord import User
from pymongo import ReturnDocument

from src.database import mongodb as db
from src.database.models.models import Profile


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger = logging.getLogger("timing")
        logger.info(f"{f.__name__}: {te - ts}")
        return result

    return wrap

def get_money(user: User):
    result = db['profile'].find_one({"owner_id": user.id})
    # TODO check if this works
    if not result:
        # TODO add init money back
        profile_of_user = Profile(user)
        profile_of_user.init_balance()
        result = db['profile'].insert_one(profile_of_user.to_mongodb())

    return result


def add_birthday(user: dict, birthday):
    return db['profile'].find_one_and_update(filter={"_id": user['_id']}, update={"$set": {'birthday': birthday}},
                                             upsert=True, return_document=ReturnDocument.AFTER)


def update_money(user: dict, money_update):
    new_balance = max(user['balance'] + money_update, 0)
    return db['profile'].find_one_and_update(filter={"_id": user['_id']}, update={"$set": {'balance': new_balance}},
                                             upsert=True, return_document=ReturnDocument.AFTER)


@timing
def get_profile(user: User = None, user_id: int = None, username: str = None):
    if user is not None:
        return db['profile'].find_one({"owner_id": user.id})
    if user_id is not None:
        return db['profile'].find_one({"owner_id": user_id})
    if username is not None:
        return db['profile'].find_one({"owner": username})


def update_active_playlist(profile: dict, value):
    return db['profile'].find_one_and_update(filter={"_id": profile['_id']},
                                             update={"$set": {"active_playlist": value}},
                                             upsert=True, return_document=ReturnDocument.AFTER)
