# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
                                        AllowAny, PermissionComponent)


class IsAttachmentOwnerPerm(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if obj and obj.owner and request.user.is_authenticated():
            return request.user == obj.owner
        return False


class UserStoryAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_us') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_us')
    update_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_us') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class TaskAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_tasks') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_task')
    update_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_task') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class IssueAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_issues') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_issue')
    update_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_issue') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class WikiAttachmentPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_wiki_pages') | IsAttachmentOwnerPerm()
    create_perms = HasProjectPerm('modify_wiki_page')
    update_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    partial_update_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    destroy_perms = HasProjectPerm('modify_wiki_page') | IsAttachmentOwnerPerm()
    list_perms = AllowAny()


class RawAttachmentPerm(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        is_owner = IsAttachmentOwnerPerm().check_permissions(request, view, obj)
        if obj.content_type.app_label == "userstories" and obj.content_type.model == "userstory":
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
