# -*- coding: utf-8 -*-

from rest_framework import permissions

from greenmine.projects.models import Membership


def has_project_perm(user, project, perm):
    if user.is_authenticated():
        try:
            membership = Membership.objects.get(project=project, user=user)
            if membership.role.permissions.filter(codename=perm).count() > 0:
                return True

        except Membership.DoesNotExist:
            pass

    return False


class BasePermission(permissions.BasePermission):
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


