# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC
#

from typing import Callable
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.db import IntegrityError
from django.db import transaction as tx
from django.utils.translation import gettext_lazy as _

from taiga.base import exceptions as exc
from taiga.base.mails import mail_builder
from taiga.users.models import User
from taiga.users.serializers import UserAdminSerializer
from taiga.users.services import get_and_validate_user
from taiga.projects.services.invitations import get_membership_by_token

from .exceptions import AuthenticationFailed, InvalidToken, TokenError
from .settings import api_settings
from .tokens import RefreshToken, CancelToken, UntypedToken
from .signals import user_registered as user_registered_signal


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


#####################
## REGISTER SERVICES
#####################

def send_register_email(user) -> bool:
    """
    Given a user, send register welcome email
    message to specified user.
    """
    cancel_token = CancelToken.for_user(user)
    context = {"user": user, "cancel_token": str(cancel_token)}
    email = mail_builder.registered_user(user, context)
    return bool(email.send())


def is_user_already_registered(*, username:str, email:str) -> (bool, str):
    """
    Checks if a specified user is already registred.

    Returns a tuple containing a boolean value that indicates if the user exists
    and in case he does whats the duplicated attribute
    """
    user_model = get_user_model()
    if user_model.objects.filter(username__iexact=username).exists():
        return (True, _("Username is already in use."))

    if user_model.objects.filter(email__iexact=email).exists():
        return (True, _("Email is already in use."))

    return (False, None)


@tx.atomic
def public_register(username:str, password:str, email:str, full_name:str):
    """
    Given a parsed parameters, try register a new user
    knowing that it follows a public register flow.

    This can raise `exc.IntegrityError` exceptions in
    case of conflics found.

    :returns: User
    """

    is_registered, reason = is_user_already_registered(username=username, email=email)
    if is_registered:
        raise exc.WrongArguments(reason)

    user_model = get_user_model()
    user = user_model(username=username,
                      email=email,
                      email_token=str(uuid.uuid4()),
                      new_email=email,
                      verified_email=False,
                      full_name=full_name,
                      read_new_terms=True)
    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        raise exc.WrongArguments(_("User is already registered."))

    send_register_email(user)
    user_registered_signal.send(sender=user.__class__, user=user)
    return user


@tx.atomic
def private_register_for_new_user(token:str, username:str, email:str,
                                  full_name:str, password:str):
    """
    Given a inviation token, try register new user matching
    the invitation token.
    """
    is_registered, reason = is_user_already_registered(username=username, email=email)
    if is_registered:
        raise exc.WrongArguments(reason)

    user_model = get_user_model()
    user = user_model(username=username,
                      email=email,
                      full_name=full_name,
                      email_token=str(uuid.uuid4()),
                      new_email=email,
                      verified_email=False,
                      read_new_terms=True)

    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        raise exc.WrongArguments(_("Error while creating new user."))

    membership = get_membership_by_token(token)
    membership.user = user
    membership.save(update_fields=["user"])
    send_register_email(user)
    user_registered_signal.send(sender=user.__class__, user=user)

    return user
