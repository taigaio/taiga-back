# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import abc
import inspect

from functools import reduce

from taiga.permissions.services import user_has_perm, is_project_admin

from django.utils.translation import gettext as _


######################################################################
# Base permissiones definition
######################################################################

class ResourcePermission(object):
    """
    Base class for define resource permissions.
    """

    enough_perms = None
    global_perms = None
    retrieve_perms = None
    create_perms = None
    update_perms = None
    destroy_perms = None
    list_perms = None

    def __init__(self, request, view):
        self.request = request
        self.view = view

    def check_permissions(self, action:str, obj:object=None):
        permset = getattr(self, "{}_perms".format(action))

        if isinstance(permset, (list, tuple)):
            permset = reduce(lambda acc, v: acc & v, permset)
        elif permset is None:
            # Use empty operator that always return true with
            # empty components.
            permset = And()
        elif isinstance(permset, PermissionComponent):
            # Do nothing
            pass
        elif inspect.isclass(permset) and issubclass(permset, PermissionComponent):
            permset = permset()
        else:
            raise RuntimeError(_("Invalid permission definition."))

        if self.global_perms:
            permset = (self.global_perms & permset)

        if self.enough_perms:
            permset = (self.enough_perms | permset)

        return permset.check_permissions(request=self.request,
                                         view=self.view,
                                         obj=obj)


class PermissionComponent(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def check_permissions(self, request, view, obj=None):
        pass

    def __invert__(self):
        return Not(self)

    def __and__(self, component):
        return And(self, component)

    def __or__(self, component):
        return Or(self, component)


class PermissionOperator(PermissionComponent):
    """
    Base class for all logical operators for compose
    components.
    """

    def __init__(self, *components):
        self.components = tuple(components)


class Not(PermissionOperator):
    """
    Negation operator as permission composable component.
    """

    # Overwrites the default constructor for fix
    # to one parameter instead of variable list of them.
    def __init__(self, component):
        super().__init__(component)

    def check_permissions(self, *args, **kwargs):
        component = self.components[0]
        return (not component.check_permissions(*args, **kwargs))


class Or(PermissionOperator):
    """
    Or logical operator as permission component.
    """

    def check_permissions(self, *args, **kwargs):
        valid = False

        for component in self.components:
            if component.check_permissions(*args, **kwargs):
                valid = True
                break

        return valid


class And(PermissionOperator):
    """
    And logical operator as permission component.
    """

    def check_permissions(self, *args, **kwargs):
        valid = True

        for component in self.components:
            if not component.check_permissions(*args, **kwargs):
                valid = False
                break

        return valid


######################################################################
# Generic components.
######################################################################

class AllowAny(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return True


class DenyAll(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return False


class IsAuthenticated(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return request.user and request.user.is_authenticated


class IsSuperUser(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class HasProjectPerm(PermissionComponent):
    def __init__(self, perm, *components):
        self.project_perm = perm
        super().__init__(*components)

    def check_permissions(self, request, view, obj=None):
        return user_has_perm(request.user, self.project_perm, obj)


class IsProjectAdmin(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        return is_project_admin(request.user, obj)


class IsObjectOwner(PermissionComponent):
    def check_permissions(self, request, view, obj=None):
        if obj.owner is None:
            return False

        return obj.owner == request.user


######################################################################
# Generic permissions.
######################################################################

class AllowAnyPermission(ResourcePermission):
    enough_perms = AllowAny()


class IsAuthenticatedPermission(ResourcePermission):
    enough_perms = IsAuthenticated()


class TaigaResourcePermission(ResourcePermission):
    enough_perms = IsSuperUser()
