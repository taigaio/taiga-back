# -*- coding: utf-8 -*-

import base64
import re

from django.core import signing
from django.db.models import get_model
from rest_framework.authentication import BaseAuthentication

import taiga.base.exceptions as exc


class Session(BaseAuthentication):
    """
    Same as rest_framework.authentication.SessionAuthentication
    but without csrf.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        http_request = request._request
        user = getattr(http_request, 'user', None)

        if not user or not user.is_active:
            return None

        return (user, None)


def get_token_for_user(user):
    data = {"user_id": user.id}
    return signing.dumps(data)


def get_user_for_token(token):
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
    Stateless authentication system partially based on oauth.
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
