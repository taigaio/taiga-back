# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
