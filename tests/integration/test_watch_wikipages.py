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


def test_watch_wikipage(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    url = reverse("wiki-watch", args=(wikipage.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_wikipage(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    url = reverse("wiki-watch", args=(wikipage.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_wikipage_watchers(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    f.WatchedFactory.create(content_object=wikipage, user=user)
    url = reverse("wiki-watchers-list", args=(wikipage.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_wikipage_watcher(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    watch = f.WatchedFactory.create(content_object=wikipage, user=user)
    url = reverse("wiki-watchers-detail", args=(wikipage.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id


def test_get_wikipage_watchers(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    url = reverse("wiki-detail", args=(wikipage.id,))

    f.WatchedFactory.create(content_object=wikipage, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['total_watchers'] == 1


def test_get_wikipage_is_watcher(client):
    user = f.UserFactory.create()
    wikipage = f.WikiPageFactory(owner=user)
    f.MembershipFactory.create(project=wikipage.project, user=user, is_admin=True)
    url_detail = reverse("wiki-detail", args=(wikipage.id,))
    url_watch = reverse("wiki-watch", args=(wikipage.id,))
    url_unwatch = reverse("wiki-unwatch", args=(wikipage.id,))

    client.login(user)

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_watchers'] == 0
    assert response.data['is_watcher'] == False

    response = client.post(url_watch)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_watchers'] == 1
    assert response.data['is_watcher'] == True

    response = client.post(url_unwatch)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_watchers'] == 0
    assert response.data['is_watcher'] == False
