# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

        data_keys = request.DATA.keys()

        if (not services.user_has_perm(request.user, self.comment_perm, project) and
            "comment" in data_keys):
                # User can't comment but there is a comment in the request
                #raise exc.PermissionDenied(_("You don't have permissions to comment this."))
                return False

        if (not services.user_has_perm(request.user, self.update_perm, project) and
            len(data_keys - "comment")):
                # User can't update but there is a change in the request
                #raise exc.PermissionDenied(_("You don't have permissions to update this."))
                return False

        return True
