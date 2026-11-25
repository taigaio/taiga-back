# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import ipaddress

from django.conf import settings

from taiga.base import throttling


def _normalize_ip(value):
    if not isinstance(value, str):
        return None
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return None
    if isinstance(address, ipaddress.IPv6Address):
        if address.scope_id:
            return None
        address = address.ipv4_mapped or address
    return str(address)


class LoginFailRateThrottle(throttling.ThrottleByActionMixin, throttling.SimpleRateThrottle):
    scope = "login-fail"
    throttled_actions = ["create", "refresh", "verify"]

    def throttle_success(self, request, view):
        return True

    def get_cache_key(self, request, view):
        peer = _normalize_ip(request.META.get("REMOTE_ADDR"))
        ident = peer
        whitelistable = True
        if peer and peer in map(_normalize_ip, settings.AUTH_THROTTLE_TRUSTED_PROXIES):
            forwarded = _normalize_ip(request.META.get("HTTP_X_FORWARDED_FOR"))
            if forwarded is None:
                whitelistable = False
            else:
                ident = forwarded

        if whitelistable and ident is not None and throttling.is_whitelisted(ident):
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def has_to_finalize(self, request, response, view):
        return (
            super().has_to_finalize(request, response, view)
            and hasattr(self, "history")
            and getattr(self, "key", None) is not None
        )

    def finalize(self, request, response, view):
        if response.status_code in [400, 401]:
            self.history.insert(0, self.now)
            self.cache.set(self.key, self.history, self.duration)


class RegisterSuccessRateThrottle(throttling.GlobalThrottlingMixin, throttling.ThrottleByActionMixin, throttling.SimpleRateThrottle):
    scope = "register-success"
    throttled_actions = ["register"]

    def throttle_success(self, request, view):
        return True

    def finalize(self, request, response, view):
        if response.status_code == 201:
            self.history.insert(0, self.now)
            self.cache.set(self.key, self.history, self.duration)

