# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps

from taiga.base.api.permissions import PermissionComponent

from . import services


######################################################################
# Generic perms
######################################################################

class HasProjectPerm(PermissionComponent):
    def __init__(self, perm, *components):
        self.project_perm = perm
        super().__init__(*components)

    def check_permissions(self, request, view, obj=None):
        return services.user_has_perm(request.user, self.project_perm, obj)


class IsObjectOwner(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if obj.owner is None:
            return False

        return obj.owner == request.user


######################################################################
# Project Perms
######################################################################

class IsProjectAdmin(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return services.is_project_admin(request.user, obj)


######################################################################
# Common perms for stories, tasks and issues
######################################################################

class CommentAndOrUpdatePerm(PermissionComponent):
    def __init__(self, update_perm, comment_perm, *components):
        self.update_perm = update_perm
        self.comment_perm = comment_perm
        super().__init__(*components)

    def check_permissions(self, request, view, obj=None):
        if not obj:
            return False

        project_id = request.DATA.get('project', None)
        if project_id and obj.project_id != project_id:
            project = apps.get_model("projects", "Project").objects.get(pk=project_id)
        else:
            project = obj.project

        data_keys = set(request.DATA.keys()) - {"version"}
        just_a_comment = data_keys == {"comment"}

        if (just_a_comment and services.user_has_perm(request.user, self.comment_perm, project)):
            return True

        return services.user_has_perm(request.user, self.update_perm, project)
