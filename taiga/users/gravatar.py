# -*- coding: utf-8 -*-
import hashlib


def get_gravatar_id(email: str) -> str:
    """Get the gravatar id associated to an email.

    :return: Gravatar id.
    """

    return hashlib.md5(email.lower().encode()).hexdigest()

def get_user_gravatar_id(user: object) -> str:
    """Get the gravatar id associated to a user.

    :return: Gravatar id.
    """
    if user and user.email:
        return get_gravatar_id(user.email)

    return None
