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


def test_watch_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-watch", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-watch", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_issue_watchers(client):
    user = f.UserFactory.create()
    issue = f.IssueFactory(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    f.WatchedFactory.create(content_object=issue, user=user)
    url = reverse("issue-watchers-list", args=(issue.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_issue_watcher(client):
    user = f.UserFactory.create()
    issue = f.IssueFactory(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    watch = f.WatchedFactory.create(content_object=issue, user=user)
    url = reverse("issue-watchers-detail", args=(issue.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id


def test_get_issue_watchers(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-detail", args=(issue.id,))

    f.WatchedFactory.create(content_object=issue, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['watchers'] == [user.id]
    assert response.data['total_watchers'] == 1


def test_get_issue_is_watcher(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url_detail = reverse("issues-detail", args=(issue.id,))
    url_watch = reverse("issues-watch", args=(issue.id,))
    url_unwatch = reverse("issues-unwatch", args=(issue.id,))

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


def test_remove_issue_watcher(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    issue = f.IssueFactory(project=project,
                           status__project=project,
                           severity__project=project,
                           priority__project=project,
                           type__project=project,
                           milestone__project=project)

    issue.add_watcher(user)
    role = f.RoleFactory.create(project=project, permissions=['modify_issue', 'view_issues'])
    f.MembershipFactory.create(project=project, user=user, role=role)

    url = reverse("issues-detail", args=(issue.id,))

    client.login(user)

    data = {"version": issue.version, "watchers": []}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data['watchers'] == []
    assert response.data['is_watcher'] == False
