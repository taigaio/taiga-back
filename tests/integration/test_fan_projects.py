# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
from django.urls import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_like_project(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("projects-like", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unlike_project(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("projects-unlike", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_project_fans(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.LikeFactory.create(content_object=project, user=user)
    url = reverse("project-fans-list", args=(project.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_project_fan(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    like = f.LikeFactory.create(content_object=project, user=user)
    url = reverse("project-fans-detail", args=(project.id, like.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == like.user.id


def test_get_project_is_fan(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url_detail = reverse("projects-detail", args=(project.id,))
    url_like = reverse("projects-like", args=(project.id,))
    url_unlike = reverse("projects-unlike", args=(project.id,))

    client.login(user)

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_fans'] == 0
    assert response.data['is_fan'] == False

    response = client.post(url_like)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_fans'] == 1
    assert response.data['is_fan'] == True

    response = client.post(url_unlike)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_fans'] == 0
    assert response.data['is_fan'] == False
