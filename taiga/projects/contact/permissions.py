# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import PermissionComponent
from taiga.base.api.permissions import TaigaResourcePermission


class IsContactActivated(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if not request.user.is_authenticated or not obj.project.is_contact_activated:
            return False

        if obj.project.is_private:
            return obj.project.cached_memberships_for_user(request.user)

        return True


class ContactPermission(TaigaResourcePermission):
    create_perms = IsContactActivated()
