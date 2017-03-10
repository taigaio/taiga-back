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
