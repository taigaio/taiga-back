# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api.permissions import (TaigaResourcePermission, HasProjectPerm,
                                        AllowAny, PermissionComponent)


class IsAttachmentOwnerPerm(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if obj and obj.owner and request.user.is_authenticated:
            return request.user == obj.owner
        return False

class CommentAttachmentPerm(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if obj.from_comment:
            return True
        return False


class EpicAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_epics') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_epic') | (CommentAttachmentPerm() & HasProjectPerm('comment_epic'))
    update_perms = HasProjectPerm('modify_epic') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_epic') | IsAttachmentOwnerPerm()
    bulk_update_order_perms = HasProjectPerm('modify_epic') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_epic') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class UserStoryAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_us') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_us') | (CommentAttachmentPerm() & HasProjectPerm('comment_us'))
    update_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    bulk_update_order_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class TaskAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_tasks') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_task') | (CommentAttachmentPerm() & HasProjectPerm('comment_task'))
    update_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    bulk_update_order_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class IssueAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_issues') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_issue') | (CommentAttachmentPerm() & HasProjectPerm('comment_issue'))
    update_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    bulk_update_order_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class WikiAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_wiki_pages') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_wiki_page') | (CommentAttachmentPerm() & HasProjectPerm('comment_wiki_page'))
    update_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    bulk_update_order_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class RawAttachmentPerm(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        is_owner = IsAttachmentOwnerPerm().check_permissions(request, view, obj)
        if obj.content_type.app_label == "epics" and obj.content_type.model == "epic":
            return EpicAttachmentPermission(request, view).check_permissions('retrieve', obj) or is_owner
        elif obj.content_type.app_label == "userstories" and obj.content_type.model == "userstory":
            return UserStoryAttachmentPermission(request, view).check_permissions('retrieve', obj) or is_owner
        elif obj.content_type.app_label == "tasks" and obj.content_type.model == "task":
            return TaskAttachmentPermission(request, view).check_permissions('retrieve', obj) or is_owner
        elif obj.content_type.app_label == "issues" and obj.content_type.model == "issue":
            return IssueAttachmentPermission(request, view).check_permissions('retrieve', obj) or is_owner
        elif obj.content_type.app_label == "wiki" and obj.content_type.model == "wikipage":
            return WikiAttachmentPermission(request, view).check_permissions('retrieve', obj) or is_owner
        return False


class RawAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = RawAttachmentPerm()
