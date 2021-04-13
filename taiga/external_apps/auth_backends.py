# -*- coding: utf-8 -*-
import re

from taiga.base.api.authentication import BaseAuthentication

from . import services

class Token(BaseAuthentication):
    auth_rx = re.compile(r"^Application (.+)$")

    def authenticate(self, request):
        if "HTTP_AUTHORIZATION" not in request.META:
            return None

        token_rx_match = self.auth_rx.search(request.META["HTTP_AUTHORIZATION"])
        if not token_rx_match:
            return None

        token = token_rx_match.group(1)
        user = services.get_user_for_application_token(token)

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
