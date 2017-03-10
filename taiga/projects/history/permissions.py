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

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        IsProjectAdmin, AllowAny,
                                        IsObjectOwner, PermissionComponent)

from taiga.permissions.services import is_project_admin
from taiga.projects.history.services import get_model_from_key, get_pk_from_key


class IsCommentDeleter(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return obj.delete_comment_user and obj.delete_comment_user.get("pk", "not-pk") == request.user.pk


class IsCommentOwner(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return obj.user and obj.user.get("pk", "not-pk") == request.user.pk


class IsCommentProjectAdmin(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        model = get_model_from_key(obj.key)
        pk = get_pk_from_key(obj.key)
        project = model.objects.get(pk=pk)
        return is_project_admin(request.user, project)


class EpicHistoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    edit_comment_perms =  IsCommentProjectAdmin() | IsCommentOwner()
    delete_comment_perms = IsCommentProjectAdmin() | IsCommentOwner()
    undelete_comment_perms = IsCommentProjectAdmin() | IsCommentDeleter()
    comment_versions_perms = IsCommentProjectAdmin() | IsCommentOwner()


class UserStoryHistoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    edit_comment_perms =  IsCommentProjectAdmin() | IsCommentOwner()
    delete_comment_perms = IsCommentProjectAdmin() | IsCommentOwner()
    undelete_comment_perms = IsCommentProjectAdmin() | IsCommentDeleter()
    comment_versions_perms = IsCommentProjectAdmin() | IsCommentOwner()


class TaskHistoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    edit_comment_perms =  IsCommentProjectAdmin() | IsCommentOwner()
    delete_comment_perms = IsCommentProjectAdmin() | IsCommentOwner()
    undelete_comment_perms = IsCommentProjectAdmin() | IsCommentDeleter()
    comment_versions_perms = IsCommentProjectAdmin() | IsCommentOwner()


class IssueHistoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    edit_comment_perms =  IsCommentProjectAdmin() | IsCommentOwner()
    delete_comment_perms = IsCommentProjectAdmin() | IsCommentOwner()
    undelete_comment_perms = IsCommentProjectAdmin() | IsCommentDeleter()
    comment_versions_perms = IsCommentProjectAdmin() | IsCommentOwner()


class WikiHistoryPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    edit_comment_perms =  IsCommentProjectAdmin() | IsCommentOwner()
    delete_comment_perms = IsCommentProjectAdmin() | IsCommentOwner()
    undelete_comment_perms = IsCommentProjectAdmin() | IsCommentDeleter()
    comment_versions_perms = IsCommentProjectAdmin() | IsCommentOwner()
