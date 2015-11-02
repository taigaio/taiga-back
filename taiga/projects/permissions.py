# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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
from taiga.base.api.permissions import HasProjectPerm
from taiga.base.api.permissions import IsAuthenticated
from taiga.base.api.permissions import IsProjectOwner
from taiga.base.api.permissions import AllowAny
from taiga.base.api.permissions import IsSuperUser
from taiga.base.api.permissions import PermissionComponent

from taiga.base import exceptions as exc
from taiga.projects.models import Membership

from . import services

class CanLeaveProject(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if not obj or not request.user.is_authenticated():
            return False

        try:
            if not services.can_user_leave_project(request.user, obj):
                raise exc.PermissionDenied(_("You can't leave the project if there are no "
                                             "more owners"))
            return True
        except Membership.DoesNotExist:
            return False


class ProjectPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    by_slug_perms = HasProjectPerm('view_project')
    create_perms = IsAuthenticated()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    modules_perms = IsProjectOwner()
    list_perms = AllowAny()
    stats_perms = HasProjectPerm('view_project')
    member_stats_perms = HasProjectPerm('view_project')
    issues_stats_perms = HasProjectPerm('view_project')
    regenerate_userstories_csv_uuid_perms = IsProjectOwner()
    regenerate_issues_csv_uuid_perms = IsProjectOwner()
    regenerate_tasks_csv_uuid_perms = IsProjectOwner()
    tags_perms = HasProjectPerm('view_project')
    tags_colors_perms = HasProjectPerm('view_project')
    like_perms = IsAuthenticated() & HasProjectPerm('view_project')
    unlike_perms = IsAuthenticated() & HasProjectPerm('view_project')
    watch_perms = IsAuthenticated() & HasProjectPerm('view_project')
    unwatch_perms = IsAuthenticated() & HasProjectPerm('view_project')
    create_template_perms = IsSuperUser()
    leave_perms = CanLeaveProject()


class ProjectFansPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    list_perms = HasProjectPerm('view_project')


class ProjectWatchersPermission(TaigaResourcePermission):
    enought_perms = IsProjectOwner() | IsSuperUser()
    global_perms = None
    retrieve_perms = HasProjectPerm('view_project')
    list_perms = HasProjectPerm('view_project')


class MembershipPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_create_perms = IsProjectOwner()
    resend_invitation_perms = IsProjectOwner()


# User Stories

class PointsPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class UserStoryStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


# Tasks

class TaskStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


# Issues

class SeverityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class PriorityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class IssueStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class IssueTypePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


# Project Templates

class ProjectTemplatePermission(TaigaResourcePermission):
    retrieve_perms = AllowAny()
    create_perms = IsSuperUser()
    update_perms = IsSuperUser()
    partial_update_perms = IsSuperUser()
    destroy_perms = IsSuperUser()
    list_perms = AllowAny()
