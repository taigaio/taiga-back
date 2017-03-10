# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
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
import pytz

from datetime import datetime, timedelta
from urllib.parse import quote

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.userstories.serializers import UserStorySerializer

from .. import factories as f


pytestmark = pytest.mark.django_db


def test_update_milestone_with_userstories_list(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    sprint = f.MilestoneFactory.create(project=project, owner=user)
    f.PointsFactory.create(project=project, value=None)
    us = f.UserStoryFactory.create(project=project, owner=user)

    url = reverse("milestones-detail", args=[sprint.pk])

    form_data = {
        "name": "test",
        "user_stories": [{"id": us.id}]
    }

    client.login(user)
    response = client.json.patch(url, json.dumps(form_data))
    assert response.status_code == 200


def test_list_milestones_taiga_info_headers(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)

    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=False)
    f.MilestoneFactory.create(owner=user, closed=False)

    url = reverse("milestones-list")

    client.login(project.owner)
    response1 = client.json.get(url)
    response2 = client.json.get(url, {"project": project.id})

    assert response1.status_code == 200
    assert "taiga-info-total-closed-milestones" in response1["access-control-expose-headers"]
    assert "taiga-info-total-opened-milestones" in response1["access-control-expose-headers"]
    assert response1.has_header("Taiga-Info-Total-Closed-Milestones") == False
    assert response1.has_header("Taiga-Info-Total-Opened-Milestones") == False

    assert response2.status_code == 200
    assert "taiga-info-total-closed-milestones" in response2["access-control-expose-headers"]
    assert "taiga-info-total-opened-milestones" in response2["access-control-expose-headers"]
    assert response2.has_header("Taiga-Info-Total-Closed-Milestones") == True
    assert response2.has_header("Taiga-Info-Total-Opened-Milestones") == True
    assert response2["taiga-info-total-closed-milestones"] == "3"
    assert response2["taiga-info-total-opened-milestones"] == "1"


def test_api_filter_by_created_date__lte(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    old_milestone = f.MilestoneFactory.create(
        project=project, owner=user, created_date=one_day_ago
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)

    url = reverse("milestones-list") + "?created_date__lte=%s" % (
        quote(milestone.created_date.isoformat())
    )

    client.login(milestone.owner)
    response = client.get(url)
    number_of_milestones = len(response.data)

    assert response.status_code == 200
    assert number_of_milestones == 2


def test_api_filter_by_modified_date__gte(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    older_milestone = f.MilestoneFactory.create(
        project=project, owner=user, created_date=one_day_ago
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)
    # we have to refresh as it slightly differs
    milestone.refresh_from_db()

    assert older_milestone.modified_date < milestone.modified_date

    url = reverse("milestones-list") + "?modified_date__gte=%s" % (
        quote(milestone.modified_date.isoformat())
    )

    client.login(milestone.owner)
    response = client.get(url)
    number_of_milestones = len(response.data)

    assert response.status_code == 200
    assert number_of_milestones == 1
    assert response.data[0]["slug"] == milestone.slug


@pytest.mark.parametrize("field_name", [
    "estimated_start", "estimated_finish"
])
def test_api_filter_by_milestone__estimated_start_and_end(client, field_name):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)

    assert hasattr(milestone, field_name)
    date = getattr(milestone, field_name)
    before = (date - timedelta(days=1)).isoformat()
    after = (date + timedelta(days=1)).isoformat()

    client.login(milestone.owner)

    expections = {
        field_name + "__gte=" + quote(before): 1,
        field_name + "__gte=" + quote(after): 0,
        field_name + "__lte=" + quote(before): 0,
        field_name + "__lte=" + quote(after): 1
    }

    for param, expection in expections.items():
        url = reverse("milestones-list") + "?" + param
        response = client.get(url)
        number_of_milestones = len(response.data)

        assert response.status_code == 200
        assert number_of_milestones == expection, param
        if number_of_milestones > 0:
            assert response.data[0]["slug"] == milestone.slug
