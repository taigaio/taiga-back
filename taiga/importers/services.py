# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from taiga.users.models import User
from taiga.projects.models import Membership

from taiga.permissions.choices import ANON_PERMISSIONS


def resolve_users_bindings(users_bindings):
    new_users_bindings = {}
    for key,value in users_bindings.items():
        try:
            user_key = int(key)
        except ValueError:
            user_key = key

        if isinstance(value, str):
            try:
                new_users_bindings[user_key] = User.objects.get(email__iexact=value)
            except User.MultipleObjectsReturned:
                new_users_bindings[user_key] = User.objects.get(email=value)
            except User.DoesNotExist:
                new_users_bindings[user_key] = None
        else:
            new_users_bindings[user_key] = User.objects.get(id=value)
    return new_users_bindings


def create_memberships(users_bindings, project, creator, role_name):
    for user in users_bindings.values():
        if Membership.objects.filter(project=project, user=user).count() > 0:
            continue
        Membership.objects.create(
            user=user,
            project=project,
            role=project.get_roles().get(slug=role_name),
            is_admin=False,
            invited_by=creator,
        )


def set_base_permissions_for_project(project):
    if project.is_private:
        return

    anon_permissions = list(
        map(lambda perm: perm[0], ANON_PERMISSIONS))
    project.anon_permissions = list(
        set((project.anon_permissions or []) + anon_permissions))
    project.public_permissions = list(
        set((project.public_permissions or []) + anon_permissions))
    project.save()
