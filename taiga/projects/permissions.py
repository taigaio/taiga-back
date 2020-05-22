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

from django.utils.translation import ugettext as _

from taiga.base.api.permissions import TaigaResourcePermission
from taiga.base.api.permissions import IsAuthenticated
from taiga.base.api.permissions import AllowAny
from taiga.base.api.permissions import IsSuperUser
from taiga.base.api.permissions import IsObjectOwner
from taiga.base.api.permissions import PermissionComponent

from taiga.base import exceptions as exc

from taiga.permissions.permissions import HasProjectPerm
from taiga.permissions.permissions import IsProjectAdmin

from . import models
from . import services


class CanLeaveProject(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if not obj or not request.user.is_authenticated:
            return False

        try:
            if not services.can_user_leave_project(request.user, obj):
                raise exc.PermissionDenied(_("You can't leave the project if you are the owner or there are "
                                             "no more admins"))
            return True
        except models.Membership.DoesNotExist:
            return False


class ProjectPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    by_slug_perms = HasProjectPerm('view_project')
    create_perms = IsAuthenticated()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    modules_perms = IsProjectAdmin()
    list_perms = AllowAny()
    change_logo_perms = IsProjectAdmin()
    remove_logo_perms = IsProjectAdmin()
    stats_perms = HasProjectPerm('view_project')
    member_stats_perms = HasProjectPerm('view_project')
    issues_stats_perms = HasProjectPerm('view_project')
    regenerate_epics_csv_uuid_perms = IsProjectAdmin()
    regenerate_userstories_csv_uuid_perms = IsProjectAdmin()
    regenerate_issues_csv_uuid_perms = IsProjectAdmin()
    regenerate_tasks_csv_uuid_perms = IsProjectAdmin()
    delete_epics_csv_uuid_perms = IsProjectAdmin()
    delete_userstories_csv_uuid_perms = IsProjectAdmin()
    delete_issues_csv_uuid_perms = IsProjectAdmin()
    delete_tasks_csv_uuid_perms = IsProjectAdmin()
    tags_perms = HasProjectPerm('view_project')
    tags_colors_perms = HasProjectPerm('view_project')
    like_perms = IsAuthenticated() & HasProjectPerm('view_project')
    unlike_perms = IsAuthenticated() & HasProjectPerm('view_project')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_project')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_project')
    create_template_perms = IsSuperUser()
    leave_perms = CanLeaveProject()
    transfer_validate_token_perms = IsAuthenticated() & HasProjectPerm('view_project')
    transfer_request_perms = IsProjectAdmin()
    transfer_start_perms = IsObjectOwner()
    transfer_reject_perms = IsAuthenticated() & HasProjectPerm('view_project')
    transfer_accept_perms = IsAuthenticated() & HasProjectPerm('view_project')
    create_tag_perms = IsProjectAdmin()
    edit_tag_perms = IsProjectAdmin()
    delete_tag_perms = IsProjectAdmin()
    mix_tags_perms = IsProjectAdmin()
    duplicate_perms = IsAuthenticated() & HasProjectPerm('view_project')


class ProjectFansPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    list_perms = HasProjectPerm('view_project')


class ProjectWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectAdmin() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    list_perms = HasProjectPerm('view_project')


class MembershipPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_create_perms = IsProjectAdmin()
    resend_invitation_perms = IsProjectAdmin()


# Epics

class EpicStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


# User Stories

class PointsPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class UserStoryStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class UserStoryDueDatePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


# Tasks

class TaskStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class TaskDueDatePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()

# Issues

class SeverityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class PriorityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class IssueStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class IssueTypePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


class IssueDueDatePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectAdmin()
    update_perms = IsProjectAdmin()
    partial_update_perms = IsProjectAdmin()
    destroy_perms = IsProjectAdmin()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectAdmin()


# Project Templates

class ProjectTemplatePermission(TaigaResourcePermission):
    retrieve_perms = AllowAny()
    create_perms = IsSuperUser()
    update_perms = IsSuperUser()
    partial_update_perms = IsSuperUser()
    destroy_perms = IsSuperUser()
    list_perms = AllowAny()
