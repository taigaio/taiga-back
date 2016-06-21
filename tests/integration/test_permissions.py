# -*- coding: utf-8 -*-
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

import pytest

from taiga.permissions import services, choices
from django.contrib.auth.models import AnonymousUser

from .. import factories

pytestmark = pytest.mark.django_db


def test_get_user_project_role():
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    project = factories.ProjectFactory()
    role = factories.RoleFactory()
    membership = factories.MembershipFactory(user=user1, project=project, role=role)

    assert services._get_user_project_membership(user1, project) == membership
    assert services._get_user_project_membership(user2, project) is None


def test_anon_get_user_project_permissions():
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    assert services.get_user_project_permissions(AnonymousUser(), project) == set(["test1"])


def test_user_get_user_project_permissions_on_public_project():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    assert services.get_user_project_permissions(user1, project) == set(["test1", "test2"])


def test_user_get_user_project_permissions_on_private_project():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    project.is_private = True
    assert services.get_user_project_permissions(user1, project) == set(["test1", "test2"])


def test_owner_get_user_project_permissions():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    project.owner = user1
    role = factories.RoleFactory(permissions=["view_us"])
    factories.MembershipFactory(user=user1, project=project, role=role)

    expected_perms = set(
        ["test1", "test2", "view_us"]
    )
    assert services.get_user_project_permissions(user1, project) == expected_perms


def test_owner_member_get_user_project_permissions():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    role = factories.RoleFactory(permissions=["test3"])
    factories.MembershipFactory(user=user1, project=project, role=role, is_admin=True)

    expected_perms = set(
        ["test1", "test2", "test3"] +
        [x[0] for x in choices.ADMINS_PERMISSIONS] +
        [x[0] for x in choices.MEMBERS_PERMISSIONS]
    )
    assert services.get_user_project_permissions(user1, project) == expected_perms


def test_member_get_user_project_permissions():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.anon_permissions = ["test1"]
    project.public_permissions = ["test2"]
    role = factories.RoleFactory(permissions=["test3"])
    factories.MembershipFactory(user=user1, project=project, role=role)

    assert services.get_user_project_permissions(user1, project) == set(["test1", "test2", "test3"])


def test_anon_user_has_perm():
    project = factories.ProjectFactory()
    project.anon_permissions = ["test"]
    assert services.user_has_perm(AnonymousUser(), "test", project) is True
    assert services.user_has_perm(AnonymousUser(), "fail", project) is False


def test_authenticated_user_has_perm_on_project():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.public_permissions = ["test"]
    assert services.user_has_perm(user1, "test", project) is True
    assert services.user_has_perm(user1, "fail", project) is False


def test_authenticated_user_has_perm_on_project_related_object():
    user1 = factories.UserFactory()
    project = factories.ProjectFactory()
    project.public_permissions = ["test"]
    us = factories.UserStoryFactory(project=project)

    assert services.user_has_perm(user1, "test", us) is True
    assert services.user_has_perm(user1, "fail", us) is False


def test_authenticated_user_has_perm_on_invalid_object():
    user1 = factories.UserFactory()
    assert services.user_has_perm(user1, "test", user1) is False
