# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import (TaigaResourcePermission, IsProjectAdmin,
                                        AllowAny, PermissionComponent)

from taiga.permissions.services import is_project_admin


class IsWebhookProjectAdmin(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return is_project_admin(request.user, obj.webhook.project)


class WebhookPermission(TaigaResourcePermission):
    retrieve_perms = IsProjectAdmin()
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    test_perms = IsProjectAdmin()


class WebhookLogPermission(TaigaResourcePermission):
    retrieve_perms = IsWebhookProjectAdmin()
    list_perms = AllowAny()
    resend_perms = IsWebhookProjectAdmin()
