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

import pytest
from unittest.mock import patch, Mock

from django.apps import apps
from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.userstories.serializers import UserStorySerializer

from .. import factories as f


pytestmark = pytest.mark.django_db

def test_update_milestone_with_userstories_list(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    member = f.MembershipFactory.create(project=project, user=user, role=role)
    sprint = f.MilestoneFactory.create(project=project, owner=user)

    points = f.PointsFactory.create(project=project, value=None)
    us = f.UserStoryFactory.create(project=project, owner=user)

    url = reverse("milestones-detail", args=[sprint.pk])

    form_data = {
        "name": "test",
        "user_stories": [UserStorySerializer(us).data]
    }

    client.login(user)
    response = client.json.patch(url, json.dumps(form_data))
    assert response.status_code == 200

