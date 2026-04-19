# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC
#

from typing import Callable

from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _

from taiga.base import exceptions as exc
from taiga.users.serializers import UserAdminSerializer
from taiga.users.services import get_and_validate_user

from .exceptions import AuthenticationFailed, InvalidToken, TokenError
from .settings import api_settings
from .tokens import RefreshToken, UntypedToken


#####################
## AUTH PLUGINS
#####################

auth_plugins = {}


def register_auth_plugin(name: str, login_func: Callable):
    auth_plugins[name] = {
        "login_func": login_func,
    }


def get_auth_plugins():
    return auth_plugins


#####################
## AUTH SERVICES
#####################

def make_auth_response_data(user):
    serializer = UserAdminSerializer(user)
    data = dict(serializer.data)

    refresh = RefreshToken.for_user(user)

    data['refresh'] = str(refresh)
    data['auth_token'] = str(refresh.access_token)

    if api_settings.UPDATE_LAST_LOGIN:
        update_last_login(None, user)

    return data


def login(username: str, password: str):
    try:
        user = get_and_validate_user(username=username, password=password)
    except exc.WrongArguments:
        raise AuthenticationFailed(
            _('No active account found with the given credentials'),
            'invalid_credentials',
        )

    # Generate data
    return make_auth_response_data(user)


def refresh_token(refresh_token: str):
    try:
        refresh = RefreshToken(refresh_token)
    except TokenError:
        raise InvalidToken()

    data = {'auth_token': str(refresh.access_token)}

    if api_settings.ROTATE_REFRESH_TOKENS:
        if api_settings.DENYLIST_AFTER_ROTATION:
            try:
                # Attempt to denylist the given refresh token
                refresh.denylist()
            except AttributeError:
                # If denylist app not installed, `denylist` method will
                # not be present
                pass

        refresh.set_jti()
        refresh.set_exp()

        data['refresh'] = str(refresh)

    return data


def verify_token(token: str):
    UntypedToken(token)
    return {}

