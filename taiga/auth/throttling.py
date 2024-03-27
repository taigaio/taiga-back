# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import throttling


class LoginFailRateThrottle(throttling.GlobalThrottlingMixin, throttling.ThrottleByActionMixin, throttling.SimpleRateThrottle):
    scope = "login-fail"
    throttled_actions = ["create", "refresh", "verify"]

    def throttle_success(self, request, view):
        return True

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

