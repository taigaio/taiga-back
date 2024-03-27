# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
