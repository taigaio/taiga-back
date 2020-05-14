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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from taiga.base.api import throttling
from ipware.ip import get_ip
from netaddr import all_matching_cidrs
from netaddr.core import AddrFormatError


class GlobalThrottlingMixin:
    """
    Define the cache key based on the user IP independently if the user is
    logged in or not.
    """
    def get_cache_key(self, request, view):
        ident = get_ip(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident
        }


# If you derive a class from this mixin you have to put this class previously
# to the base throttling class.
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


class CommonThrottle(throttling.SimpleRateThrottle):
    cache_format = "throtte_%(scope)s_%(rate)s_%(ident)s"

    def __init__(self):
        pass

    def has_to_finalize(self, request, response, view):
        return False

    def is_whitelisted(self, ident):
        for whitelisted in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_WHITELIST']:
            if isinstance(whitelisted, int) and whitelisted == ident:
                return True
            elif isinstance(whitelisted, str):
                try:
                    if all_matching_cidrs(ident, [whitelisted]) != []:
                        return True
                except(AddrFormatError, ValueError):
                    pass
        return False

    def allow_request(self, request, view):
        scope = self.get_scope(request)
        ident = self.get_ident(request)
        rates = self.get_rates(scope)

        if self.is_whitelisted(ident):
            return True

        if rates is None or rates == []:
            return True

        now = self.timer()

        waits = []
        history_writes = []

        for rate in rates:
            rate_name = rate[0]
            rate_num_requests = rate[1]
            rate_duration = rate[2]

            key = self.get_cache_key(ident, scope, rate_name)
            history = self.cache.get(key, [])

            while history and history[-1] <= now - rate_duration:
                history.pop()

            if len(history) >= rate_num_requests:
                waits.append(self.wait_time(history, rate, now))

            history_writes.append({
                "key": key,
                "history": history,
                "rate_duration": rate_duration,
            })

        if waits:
            self._wait = max(waits)
            return False

        for history_write in history_writes:
            history_write['history'].insert(0, now)
            self.cache.set(
                history_write['key'],
                history_write['history'],
                history_write['rate_duration']
            )
        return True

    def get_rates(self, scope):
        try:
            rates = self.THROTTLE_RATES[scope]
        except KeyError:
            msg = "No default throttle rate set for \"%s\" scope" % scope
            raise ImproperlyConfigured(msg)

        if rates is None:
            return []
        elif isinstance(rates, str):
            return [self.parse_rate(rates)]
        elif isinstance(rates, list):
            return list(map(self.parse_rate, rates))
        else:
            msg = "No valid throttle rate set for \"%s\" scope" % scope
            raise ImproperlyConfigured(msg)

    def parse_rate(self, rate):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        if rate is None:
            return None
        num, period = rate.split("/")
        num_requests = int(num)
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period[0]]
        return (rate, num_requests, duration)

    def get_scope(self, request):
        scope_prefix = "user" if request.user.is_authenticated else "anon"
        scope_sufix = "write" if request.method in ["POST", "PUT", "PATCH", "DELETE"] else "read"
        scope = "{}-{}".format(scope_prefix, scope_sufix)
        return scope

    def get_ident(self, request):
        if request.user.is_authenticated:
            return request.user.id
        ident = get_ip(request)
        return ident

    def get_cache_key(self, ident, scope, rate):
        return self.cache_format % { "scope": scope, "ident": ident, "rate": rate }

    def wait_time(self, history, rate, now):
        rate_num_requests = rate[1]
        rate_duration = rate[2]

        if history:
            remaining_duration = rate_duration - (now - history[-1])
        else:
            remaining_duration = rate_duration

        available_requests = rate_num_requests - len(history) + 1
        if available_requests <= 0:
            return remaining_duration

        return remaining_duration / float(available_requests)

    def wait(self):
        return self._wait


class SimpleRateThrottle(throttling.SimpleRateThrottle):
    pass
