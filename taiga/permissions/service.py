# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from .permissions import ADMINS_PERMISSIONS, MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

from django.apps import apps

def _get_user_project_membership(user, project):
    if user.is_anonymous():
        return None

    return user.cached_membership_for_project(project)


def _get_object_project(obj):
    project = None
    Project = apps.get_model("projects", "Project")
    if isinstance(obj, Project):
        project = obj
    elif obj and hasattr(obj, 'project'):
        project = obj.project
    return project


def is_project_owner(user, obj):
    project = _get_object_project(obj)
    if project is None:
        return False

    if user.id == project.owner.id:
        return True

    return False


def is_project_admin(user, obj):
    if user.is_superuser:
        return True

    project = _get_object_project(obj)
    if project is None:
        return False

    membership = _get_user_project_membership(user, project)
    if membership and membership.is_admin:
        return True

    return False


def user_has_perm(user, perm, obj=None):
    project = _get_object_project(obj)

    if not project:
        return False

    return perm in get_user_project_permissions(user, project)


def role_has_perm(role, perm):
    return perm in role.permissions


def _get_membership_permissions(membership):
    if membership and membership.role and membership.role.permissions:
        return membership.role.permissions
    return []


def get_user_project_permissions(user, project):
    membership = _get_user_project_membership(user, project)
    if user.is_superuser:
        admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        public_permissions = list(map(lambda perm: perm[0], USER_PERMISSIONS))
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    elif membership:
        if membership.is_admin:
            admins_permissions = list(map(lambda perm: perm[0], ADMINS_PERMISSIONS))
            members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        else:
            admins_permissions = []
            members_permissions = []
        members_permissions = members_permissions + _get_membership_permissions(membership)
        public_permissions = project.public_permissions if project.public_permissions is not None else []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []
    elif user.is_authenticated():
        admins_permissions = []
        members_permissions = []
        public_permissions = project.public_permissions if project.public_permissions is not None else []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []
    else:
        admins_permissions = []
        members_permissions = []
        public_permissions = []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []

    return set(admins_permissions + members_permissions + public_permissions + anon_permissions)


def set_base_permissions_for_project(project):
    if project.is_private:
        project.anon_permissions = []
        project.public_permissions = []
    else:
        # If a project is public anonymous and registered users should have at
        # least visualization permissions.
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
        project.anon_permissions = list(set((project.anon_permissions or []) + anon_permissions))
        project.public_permissions = list(set((project.public_permissions or []) + anon_permissions))
