# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
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


from taiga.base.permissions import BasePermission
from taiga.domains import get_active_domain


class ProjectPermission(BasePermission):
    get_permission = "view_project"
    post_permission = None
    put_permission = "change_project"
    patch_permission = "change_project"
    delete_permission = None
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  []

class ProjectAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in self.safe_methods:
            return True

        domain = get_active_domain()
        if request.method in ["POST", "PUT", "GET", "PATCH"]:
            return domain.user_is_staff(request.user)
        elif request.method == "DELETE":
            return domain.user_is_owner(request.user)
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.method in self.safe_methods:
            return True

        domain = get_active_domain()
        if request.method in ["POST", "PUT", "GET", "PATCH"]:
            return domain.user_is_staff(request.user)
        elif request.method == "DELETE":
            return domain.user_is_owner(request.user)
        return super().has_object_permission(request, view, obj)


class MembershipPermission(BasePermission):
    get_permission = "view_membership"
    post_permission = "add_membership"
    put_permission = "change_membership"
    patch_permission = "change_membership"
    delete_permission = "delete_membership"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class AttachmentPermission(BasePermission):
    get_permission = "view_attachment"
    post_permission = "add_attachment"
    put_permission = "change_attachment"
    patch_permission = "change_attachment"
    delete_permission = "delete_attachment"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# User Stories

class PointsPermission(BasePermission):
    get_permission = "view_points"
    post_permission = "add_points"
    put_permission = "change_points"
    patch_permission = "change_points"
    delete_permission = "delete_points"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class UserStoryStatusPermission(BasePermission):
    get_permission = "view_userstorystatus"
    post_permission = "add_userstorystatus"
    put_permission = "change_userstorystatus"
    patch_permission = "change_userstorystatus"
    delete_permission = "delete_userstorystatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Tasks

class TaskStatusPermission(BasePermission):
    get_permission = "view_taskstatus"
    post_permission = "ade_taskstatus"
    put_permission = "change_taskstatus"
    patch_permission = "change_taskstatus"
    delete_permission = "delete_taskstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Issues

class SeverityPermission(BasePermission):
    get_permission = "view_severity"
    post_permission = "add_severity"
    put_permission = "change_severity"
    patch_permission = "change_severity"
    delete_permission = "delete_severity"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class PriorityPermission(BasePermission):
    get_permission = "view_priority"
    post_permission = "add_priority"
    put_permission = "change_priority"
    patch_permission = "change_priority"
    delete_permission = "delete_priority"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueStatusPermission(BasePermission):
    get_permission = "view_issuestatus"
    post_permission = "add_issuestatus"
    put_permission = "change_issuestatus"
    patch_permission = "change_issuestatus"
    delete_permission = "delete_issuestatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class IssueTypePermission(BasePermission):
    get_permission = "view_issuetype"
    post_permission = "add_issuetype"
    put_permission = "change_issuetype"
    patch_permission = "change_issuetype"
    delete_permission = "delete_issuetype"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


class RolesPermission(BasePermission):
    get_permission = "view_role"
    post_permission = "add_role"
    put_permission = "change_role"
    patch_permission = "change_role"
    delete_permission = "delete_role"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]


# Questions

class QuestionStatusPermission(BasePermission):
    get_permission = "view_questionstatus"
    post_permission = "add_questionstatus"
    put_permission = "change_questionstatus"
    patch_permission = "change_questionstatus"
    delete_permission = "delete_questionstatus"
    safe_methods = ["HEAD", "OPTIONS"]
    path_to_project =  ["project"]
