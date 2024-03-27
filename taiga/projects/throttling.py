# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base import throttling


class MembershipsRateThrottle(throttling.ThrottleByActionMixin, throttling.UserRateThrottle):
    scope = "create-memberships"
    throttled_actions = ["create", "resend_invitation", "bulk_create"]

    def exceeded_throttling_restriction(self, request, view):
        self.created_memberships = 0
        if view.action in ["create", "resend_invitation"]:
            self.created_memberships = 1
        elif view.action == "bulk_create":
            self.created_memberships = len(request.DATA.get("bulk_memberships", []))
        return len(self.history) + self.created_memberships > self.num_requests

    def throttle_success(self, request, view):
        for i in range(self.created_memberships):
            self.history.insert(0, self.now)

        self.cache.set(self.key, self.history, self.duration)
        return True
