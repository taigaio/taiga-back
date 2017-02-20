# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.base.api import throttling


class GlobalThrottlingMixin:
    """
    Define the cache key based on the user IP independently if the user is
    logged in or not.
    """
    def get_cache_key(self, request, view):
        ident = request.META.get("HTTP_X_FORWARDED_FOR")
        if ident is None:
            ident = request.META.get("REMOTE_ADDR")

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident
        }


class ThrottleByActionMixin:
    throttled_actions = []

    def has_to_finalize(self, request, response, view):
        if super().has_to_finalize(request, response, view):
            return view.action in self.throttled_actions
        return False

    def allow_request(self, request, view):
        if view.action in self.throttled_actions:
            return super().allow_request(request, view)
        return True


class AnonRateThrottle(throttling.AnonRateThrottle):
    scope = "anon"


class UserRateThrottle(throttling.UserRateThrottle):
    scope = "user"


class SimpleRateThrottle(throttling.SimpleRateThrottle):
    pass
