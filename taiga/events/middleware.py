# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

    def process_request(self, request):
        global _local
        session_id = request.META.get("HTTP_X_SESSION_ID", None)
        _local.session_id = session_id
        request.session_id = session_id

    def process_response(self, request, response):
        global _local
        _local.session_id = None

        return response
