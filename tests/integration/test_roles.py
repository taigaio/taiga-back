# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.urls import reverse

from taiga.users.models import Role
from taiga.projects.models import Membership
from taiga.projects.models import Project

from .. import factories as f


pytestmark = pytest.mark.django_db


def test_destroy_role_and_reassign_members(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)
    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user1, role=role1, is_admin=True)
    f.MembershipFactory.create(project=project, user=user2, role=role2)

    url = reverse("roles-detail", args=[role2.pk]) + "?moveTo={}".format(role1.pk)

    client.login(user1)

    response = client.delete(url)
    assert response.status_code == 204

    qs = Role.objects.filter(project=project)
    assert qs.count() == 1

    qs = Membership.objects.filter(project=project, role_id=role2.pk)
    assert qs.count() == 0

    qs = Membership.objects.filter(project=project, role_id=role1.pk)
    assert qs.count() == 2
