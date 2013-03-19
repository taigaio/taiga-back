# -*- coding: utf-8 -*-

import uuid

def set_token(user):
    """
    Set new token for user profile.
    """

    token = unicode(uuid.uuid4())
    profile = user.get_profile()
    profile.token = token

    user.save()
    profile.save()
    return token

