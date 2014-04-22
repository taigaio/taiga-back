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
from django.db.models import get_model
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

    model_cls = get_model("users", "User")

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
