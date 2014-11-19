# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be> # Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
                                        IsAuthenticated, IsProjectOwner,
                                        AllowAny, IsSuperUser)


class ProjectPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsAuthenticated()
    update_perms = IsProjectOwner()
    partial_update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    modules_perms = IsProjectOwner()
    list_perms = AllowAny()
    stats_perms = AllowAny()
    member_stats_perms = HasProjectPerm('view_project') 
    star_perms = IsAuthenticated()
    unstar_perms = IsAuthenticated()
    issues_stats_perms = AllowAny()
    issues_filters_data_perms = AllowAny()
    tags_perms = HasProjectPerm('view_project')
    tags_colors_perms = HasProjectPerm('view_project')
    fans_perms = HasProjectPerm('view_project')
    create_template_perms = IsSuperUser()


class MembershipPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_create_perms = IsProjectOwner()
    resend_invitation_perms = IsProjectOwner()


# User Stories

class PointsPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class UserStoryStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


# Tasks

class TaskStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


# Issues

class SeverityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class PriorityPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class IssueStatusPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class IssueTypePermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()
    bulk_update_order_perms = IsProjectOwner()


class RolesPermission(TaigaResourcePermission):
    retrieve_perms = HasProjectPerm('view_project')
    create_perms = IsProjectOwner()
    update_perms = IsProjectOwner()
    destroy_perms = IsProjectOwner()
    list_perms = AllowAny()


# Project Templates

class ProjectTemplatePermission(TaigaResourcePermission):
    retrieve_perms = AllowAny()
    create_perms = IsSuperUser()
    update_perms = IsSuperUser()
    destroy_perms = IsSuperUser()
    list_perms = AllowAny()
