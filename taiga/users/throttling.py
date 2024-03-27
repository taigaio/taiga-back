# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import throttling


class UserDetailRateThrottle(throttling.GlobalThrottlingMixin, throttling.ThrottleByActionMixin, throttling.SimpleRateThrottle):
    scope = "user-detail"
    throttled_actions = ["by_username", "retrieve"]


class UserUpdateRateThrottle(throttling.ThrottleByActionMixin, throttling.UserRateThrottle):
    scope = "user-update"
    throttled_actions = ["update", "partial_update"]
