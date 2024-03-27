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


def test_watch_task(client):
    user = f.UserFactory.create()
    task = f.create_task(owner=user, milestone=None)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    url = reverse("tasks-watch", args=(task.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_task(client):
    user = f.UserFactory.create()
    task = f.create_task(owner=user, milestone=None)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    url = reverse("tasks-watch", args=(task.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_task_watchers(client):
    user = f.UserFactory.create()
    task = f.TaskFactory(owner=user)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    f.WatchedFactory.create(content_object=task, user=user)
    url = reverse("task-watchers-list", args=(task.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_task_watcher(client):
    user = f.UserFactory.create()
    task = f.TaskFactory(owner=user)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    watch = f.WatchedFactory.create(content_object=task, user=user)
    url = reverse("task-watchers-detail", args=(task.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id


def test_get_task_watchers(client):
    user = f.UserFactory.create()
    task = f.TaskFactory(owner=user)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    url = reverse("tasks-detail", args=(task.id,))

    f.WatchedFactory.create(content_object=task, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['watchers'] == [user.id]
    assert response.data['total_watchers'] == 1


def test_get_task_is_watcher(client):
    user = f.UserFactory.create()
    task = f.create_task(owner=user, milestone=None)
    f.MembershipFactory.create(project=task.project, user=user, is_admin=True)
    url_detail = reverse("tasks-detail", args=(task.id,))
    url_watch = reverse("tasks-watch", args=(task.id,))
    url_unwatch = reverse("tasks-unwatch", args=(task.id,))

    client.login(user)

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['watchers'] == []
    assert response.data['is_watcher'] == False

    response = client.post(url_watch)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['watchers'] == [user.id]
    assert response.data['is_watcher'] == True

    response = client.post(url_unwatch)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['watchers'] == []
    assert response.data['is_watcher'] == False


def test_remove_task_watcher(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    task = f.TaskFactory(project=project,
                         user_story=None,
                         status__project=project,
                         milestone__project=project)

    task.add_watcher(user)
    role = f.RoleFactory.create(project=project, permissions=['modify_task', 'view_tasks'])
    f.MembershipFactory.create(project=project, user=user, role=role)

    url = reverse("tasks-detail", args=(task.id,))

    client.login(user)

    data = {"version": task.version, "watchers": []}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data['watchers'] == []
    assert response.data['is_watcher'] == False
