# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
