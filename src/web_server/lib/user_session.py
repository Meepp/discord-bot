from typing import Optional

from flask import session, g as flaskg

from database.models.models import Profile
from database.repository import profile_repository


def session_user() -> Optional[Profile]:
    """
    Return the current authenticated user.
    :return: the current authenticated user.
    :return: None if no user is logged in.
    """
    user_id = session['user_id'] if 'user_id' in session else None
    if user_id is not None:
        if not hasattr(flaskg, 'session_user'):
            flaskg.session_user = profile_repository.get_profile(user_id=user_id)
            if flaskg.session_user is None:
                del session['user_id']

        return flaskg.session_user
    return None


def session_is_authed():
    """
    Checks if the session is authorized.
    :return:
    """
    if 'user_id' not in session:
        return False

    return session_user() is not None


def session_user_set(user: Optional[Profile]):
    """
    Set the current user associated with the session.
    If not None, session_is_authed() will return True and session_user() will return the user.
    If None, session_is_authed() will return False and session_user() will raise a ValueError.
    :param user: The user or None.
    """
    if user is None:
        del session['user_id']
    else:
        session['user_id'] = user.owner_id
