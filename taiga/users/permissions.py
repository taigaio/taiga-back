# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import TaigaResourcePermission
from taiga.base.api.permissions import IsSuperUser
from taiga.base.api.permissions import AllowAny
from taiga.base.api.permissions import IsAuthenticated
from taiga.base.api.permissions import HasProjectPerm
from taiga.base.api.permissions import IsProjectAdmin
from taiga.base.api.permissions import PermissionComponent
from django.conf import settings


class IsTheSameUser(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return obj and request.user.is_authenticated and request.user.pk == obj.pk


class CanRetrieveUser(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if settings.PRIVATE_USER_PROFILES:
            return obj and request.user and request.user.is_authenticated()

        return True


class UserPermission(TaigaResourcePermission):
    enough_perms = IsSuperUser()
    global_perms = None
    retrieve_perms = CanRetrieveUser()
    by_username_perms = retrieve_perms
    update_perms = IsTheSameUser()
    partial_update_perms = IsTheSameUser()
    destroy_perms = IsTheSameUser()
    list_perms = AllowAny()
    stats_perms = AllowAny()
    password_recovery_perms = AllowAny()
    change_password_from_recovery_perms = AllowAny()
    change_password_perms = IsAuthenticated()
    change_avatar_perms = IsAuthenticated()
    me_perms = IsAuthenticated()
    remove_avatar_perms = IsAuthenticated()
    change_email_perms = AllowAny()
    contacts_perms = AllowAny()
    liked_perms = AllowAny()
    voted_perms = AllowAny()
    watched_perms = AllowAny()
    send_verification_email_perms = IsAuthenticated()


class RolesPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
