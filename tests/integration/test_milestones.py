# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.userstories.serializers import UserStorySerializer

from .. import factories as f


pytestmark = pytest.mark.django_db


def test_update_milestone_with_userstories_list(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)
    sprint = f.MilestoneFactory.create(project=project, owner=user)
    f.PointsFactory.create(project=project, value=None)
    us = f.UserStoryFactory.create(project=project, owner=user)

    url = reverse("milestones-detail", args=[sprint.pk])

    form_data = {
        "name": "test",
        "user_stories": [UserStorySerializer(us).data]
    }

    client.login(user)
    response = client.json.patch(url, json.dumps(form_data))
    assert response.status_code == 200


def test_list_milestones_taiga_info_headers(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_owner=True)

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
