# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
