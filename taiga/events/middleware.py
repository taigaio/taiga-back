# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import threading

_local = threading.local()
_local.session_id = None


def get_current_session_id() -> str:
    """
    Get current session id for current
    request.

    This function should be used only whithin
    request context. Out of request context
    it always return None
    """

    global _local
    if not hasattr(_local, "session_id"):
        raise RuntimeError("No session identifier is found, "
                           "are you sure that session id middleware "
                           "is active?")
    return _local.session_id


class SessionIDMiddleware(object):
    """
    Middleware for extract and store a current web sesion
    identifier to thread local storage (that only avaliable for
    current thread).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        self.process_response(request, response)

        return response


    def process_request(self, request):
        global _local
        session_id = request.headers.get("x-session-id", None)
        _local.session_id = session_id
        request.session_id = session_id

    def process_response(self, request, response):
        global _local
        _local.session_id = None

        return response
