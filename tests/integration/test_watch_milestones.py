# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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
import json
from django.urls import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_watch_milestone(client):
    user = f.UserFactory.create()
    milestone = f.MilestoneFactory(owner=user)
    f.MembershipFactory.create(project=milestone.project, user=user, is_admin=True)
    url = reverse("milestones-watch", args=(milestone.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_milestone(client):
    user = f.UserFactory.create()
    milestone = f.MilestoneFactory(owner=user)
    f.MembershipFactory.create(project=milestone.project, user=user, is_admin=True)
    url = reverse("milestones-watch", args=(milestone.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_milestone_watchers(client):
    user = f.UserFactory.create()
    milestone = f.MilestoneFactory(owner=user)
    f.MembershipFactory.create(project=milestone.project, user=user, is_admin=True)
    f.WatchedFactory.create(content_object=milestone, user=user)
    url = reverse("milestone-watchers-list", args=(milestone.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_milestone_watcher(client):
    user = f.UserFactory.create()
    milestone = f.MilestoneFactory(owner=user)
    f.MembershipFactory.create(project=milestone.project, user=user, is_admin=True)
    watch = f.WatchedFactory.create(content_object=milestone, user=user)
    url = reverse("milestone-watchers-detail", args=(milestone.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id
