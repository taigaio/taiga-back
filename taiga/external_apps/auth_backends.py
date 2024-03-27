# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re

from taiga.base.api.authentication import BaseAuthentication

from . import services

class Token(BaseAuthentication):
    auth_rx = re.compile(r"^Application (.+)$")

    def authenticate(self, request):
        if "authorization" not in request.headers:
            return None

        token_rx_match = self.auth_rx.search(request.headers["authorization"])
        if not token_rx_match:
            return None

        token = token_rx_match.group(1)
        user = services.get_user_for_application_token(token)

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
