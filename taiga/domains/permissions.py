# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
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

from .models import DomainMember
from .base import get_active_domain


class DomainPermission(permissions.BasePermission):
    safe_methods = ['HEAD', 'OPTIONS', 'GET']

    def has_object_permission(self, request, view, obj):
        if request.method in self.safe_methods:
            return True

        domain = get_active_domain()
        return domain.user_is_owner(request.user)


class DomainMembersPermission(permissions.BasePermission):
    safe_methods = ['HEAD', 'OPTIONS']

    def has_permission(self, request, view):
        if request.method in self.safe_methods:
            return True

        domain = get_active_domain()
        if request.method in ["POST", "PUT", "PATCH", "GET"]:
            return domain.user_is_owner(request.user)

        return False
