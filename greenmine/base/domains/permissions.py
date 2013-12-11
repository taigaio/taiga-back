from rest_framework import permissions

from greenmine.base.domains.models import DomainMember
from greenmine.base.domains import get_active_domain


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
        else:
            return False
