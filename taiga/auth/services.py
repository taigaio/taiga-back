# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains a domain logic for authentication
process. It called services because in DDD says it.

NOTE: Python doesn't have java limitations for "everytghing
should be contained in a class". Because of that, it
not uses clasess and uses simple functions.
"""

from django.apps import apps
from django.db import transaction as tx
from django.db import IntegrityError
from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.base.mails import mail_builder
from taiga.users.serializers import UserAdminSerializer
from taiga.users.services import get_and_validate_user

from .tokens import get_token_for_user
from .signals import user_registered as user_registered_signal

auth_plugins = {}


def register_auth_plugin(name, login_func):
    auth_plugins[name] = {
        "login_func": login_func,
    }


def get_auth_plugins():
    return auth_plugins


def send_register_email(user) -> bool:
    """
    Given a user, send register welcome email
    message to specified user.
    """
    cancel_token = get_token_for_user(user, "cancel_account")
    context = {"user": user, "cancel_token": cancel_token}
    email = mail_builder.registered_user(user, context)
    return bool(email.send())


def is_user_already_registered(*, username:str, email:str) -> (bool, str):
    """
    Checks if a specified user is already registred.

    Returns a tuple containing a boolean value that indicates if the user exists
    and in case he does whats the duplicated attribute
    """

    user_model = apps.get_model("users", "User")
    if user_model.objects.filter(username=username):
        return (True, _("Username is already in use."))

    if user_model.objects.filter(email=email):
        return (True, _("Email is already in use."))

    return (False, None)


def get_membership_by_token(token:str):
    """
    Given a token, returns a membership instance
    that matches with specified token.

    If not matches with any membership NotFound exception
    is raised.
    """
    membership_model = apps.get_model("projects", "Membership")
    qs = membership_model.objects.filter(token=token)
    if len(qs) == 0:
        raise exc.NotFound(_("Token not matches any valid invitation."))
    return qs[0]


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

    user_model = apps.get_model("users", "User")
    user = user_model(username=username,
                      email=email,
                      full_name=full_name)
    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        raise exc.WrongArguments(_("User is already registered."))

    send_register_email(user)
    user_registered_signal.send(sender=user.__class__, user=user)
    return user


@tx.atomic
def private_register_for_existing_user(token:str, username:str, password:str):
    """
    Register works not only for register users, also serves for accept
    inviatations for projects as existing user.

    Given a invitation token with parsed parameters, accept inviation
    as existing user.
    """

    user = get_and_validate_user(username=username, password=password)
    membership = get_membership_by_token(token)

    try:
        membership.user = user
        membership.save(update_fields=["user"])
    except IntegrityError:
        raise exc.IntegrityError(_("Membership with user is already exists."))

    send_register_email(user)
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

    user_model = apps.get_model("users", "User")
    user = user_model(username=username,
                      email=email,
                      full_name=full_name)

    user.set_password(password)
    try:
        user.save()
    except IntegrityError:
        raise exc.WrongArguments(_("Error on creating new user."))

    membership = get_membership_by_token(token)
    membership.user = user
    membership.save(update_fields=["user"])
    send_register_email(user)
    user_registered_signal.send(sender=user.__class__, user=user)

    return user


def make_auth_response_data(user) -> dict:
    """
    Given a domain and user, creates data structure
    using python dict containing a representation
    of the logged user.
    """
    serializer = UserAdminSerializer(user)
    data = dict(serializer.data)
    data["auth_token"] = get_token_for_user(user, "authentication")
    return data


def normal_login_func(request):
    username = request.DATA.get('username', None)
    password = request.DATA.get('password', None)

    user = get_and_validate_user(username=username, password=password)
    data = make_auth_response_data(user)
    return data


register_auth_plugin("normal", normal_login_func)
