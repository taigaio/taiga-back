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

from rest_framework import permissions

from taiga.projects.models import Membership


def has_project_perm(user, project, perm):
    if user.is_authenticated():
        try:
            membership = Membership.objects.get(project=project, user=user)
            return membership.role.permissions.filter(codename=perm).exists()
        except Membership.DoesNotExist:
            pass

    return False


class Permission(permissions.BasePermission):
    """
    Base permission class.
    """
    pass


class BasePermission(Permission):
    get_permission = None
    post_permission = None
    put_permission = None
    patch_permission = None
    delete_permission = None
    safe_methods = ['HEAD', 'OPTIONS']
    path_to_project =  []

    def has_object_permission(self, request, view, obj):
        # Safe method
        if request.method in self.safe_methods:
            return True

        # Object owner
        if getattr(obj, "owner", None) == request.user:
            return True

        project_obj = obj
        for attrib in self.path_to_project:
            project_obj = getattr(project_obj, attrib)

        # Project owner
        if project_obj.owner == request.user:
            return True

        # Members permissions
        if request.method == "GET":
            return has_project_perm(request.user, project_obj, self.get_permission)
        elif request.method == "POST":
            return has_project_perm(request.user, project_obj, self.post_permission)
        elif request.method == "PUT":
            return has_project_perm(request.user, project_obj, self.put_permission)
        elif request.method == "PATCH":
            return has_project_perm(request.user, project_obj, self.patch_permission)
        elif request.method == "DELETE":
            return has_project_perm(request.user, project_obj, self.delete_permission)

        return False


