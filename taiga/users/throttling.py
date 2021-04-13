# -*- coding: utf-8 -*-
from taiga.base import throttling


class UserDetailRateThrottle(throttling.GlobalThrottlingMixin, throttling.ThrottleByActionMixin, throttling.SimpleRateThrottle):
    scope = "user-detail"
    throttled_actions = ["by_username", "retrieve"]


class UserUpdateRateThrottle(throttling.ThrottleByActionMixin, throttling.UserRateThrottle):
    scope = "user-update"
    throttled_actions = ["update", "partial_update"]
