# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
Authentication backends for rest framework.

This module exposes two backends: session and token.

The first (session) is a modified version of standard
session authentication backend of restframework with
csrf token disabled.

And the second (token) implements own version of oauth2
like authentiacation but with selfcontained tokens. Thats
makes authentication totally stateles.

It uses django signing framework for create new
selfcontained tokens. This trust tokes from external
fraudulent modifications.
"""

import base64
import re

from django.core import signing
from django.apps import apps
from rest_framework.authentication import BaseAuthentication
from taiga.base import exceptions as exc


class Session(BaseAuthentication):
    """
    Session based authentication like the standard
    `rest_framework.authentication.SessionAuthentication`
    but with csrf disabled (for obvious reasons because
    it is for api.

    NOTE: this is only for api web interface. Is not used
    for common api usage and should be disabled on production.
    """

    def authenticate(self, request):
        http_request = request._request
        user = getattr(http_request, 'user', None)

        if not user or not user.is_active:
            return None

        return (user, None)


def get_token_for_user(user):
    """
    Generate a new signed token containing
    a specified user.
    """
    data = {"user_id": user.id}
    return signing.dumps(data)


def get_user_for_token(token):
    """
    Given a selfcontained token, try parse and
    unsign it.

    If token passes a validation, returns
    a user instance corresponding with user_id stored
    in the incoming token.
    """
    try:
        data = signing.loads(token)
    except signing.BadSignature:
        raise exc.NotAuthenticated("Invalid token")

    model_cls = apps.get_model("users", "User")

    try:
        user = model_cls.objects.get(pk=data["user_id"])
    except model_cls.DoesNotExist:
        raise exc.NotAuthenticated("Invalid token")
    else:
        return user


class Token(BaseAuthentication):
    """
    Self-contained stateles authentication implementatrion
    that work similar to oauth2.
    It uses django signing framework for trust data stored
    in the token.
    """

    auth_rx = re.compile(r"^Bearer (.+)$")

    def authenticate(self, request):
        if "HTTP_AUTHORIZATION" not in request.META:
            return None

        token_rx_match = self.auth_rx.search(request.META["HTTP_AUTHORIZATION"])
        if not token_rx_match:
            return None

        token = token_rx_match.group(1)
        user = get_user_for_token(token)
        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
