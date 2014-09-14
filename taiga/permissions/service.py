# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

from taiga.projects.models import Membership, Project
from .permissions import OWNERS_PERMISSIONS, MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS


def _get_user_project_membership(user, project):
    if user.is_anonymous():
        return None

    try:
        return Membership.objects.get(user=user, project=project)
    except Membership.DoesNotExist:
        return None

def _get_object_project(obj):
    project = None

    if isinstance(obj, Project):
        project = obj
    elif obj and hasattr(obj, 'project'):
        project = obj.project
    return project


def is_project_owner(user, obj):
    if user.is_superuser:
        return True

    project = _get_object_project(obj)

    if project and project.owner == user:
        return True

    membership = _get_user_project_membership(user, project)
    if membership and membership.is_owner:
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
        owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        public_permissions = list(map(lambda perm: perm[0], USER_PERMISSIONS))
        anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    elif project.owner == user:
        owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
        members_permissions = list(map(lambda perm: perm[0], MEMBERS_PERMISSIONS))
        public_permissions = project.public_permissions if project.public_permissions is not None else []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []
    elif membership:
        if membership.is_owner:
            owner_permissions = list(map(lambda perm: perm[0], OWNERS_PERMISSIONS))
        else:
            owner_permissions = []
        members_permissions = _get_membership_permissions(membership)
        public_permissions = project.public_permissions if project.public_permissions is not None else []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []
    elif user.is_authenticated():
        owner_permissions = []
        members_permissions = []
        public_permissions = project.public_permissions if project.public_permissions is not None else []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []
    else:
        owner_permissions = []
        members_permissions = []
        public_permissions = []
        anon_permissions = project.anon_permissions if project.anon_permissions is not None else []

    return set(owner_permissions + members_permissions + public_permissions + anon_permissions)
