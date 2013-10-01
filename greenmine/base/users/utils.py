# -*- coding: utf-8 -*-

import uuid


def set_token(user):
    """
    Set new token for user profile.
    """

    token = unicode(uuid.uuid4())
    user.token = token
    user.save()
    return token
