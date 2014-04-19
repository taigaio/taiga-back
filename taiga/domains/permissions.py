# Copyright 2014 Andrey Antukh <niwi@niwi.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# y ou may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
