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


def test_upvote_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-upvote", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_downvote_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-downvote", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_issue_voters(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    f.VoteFactory.create(content_object=issue, user=user)
    url = reverse("issue-voters-list", args=(issue.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id

def test_get_issue_voter(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    vote = f.VoteFactory.create(content_object=issue, user=user)
    url = reverse("issue-voters-detail", args=(issue.id, vote.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == vote.user.id

def test_get_issue_votes(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    url = reverse("issues-detail", args=(issue.id,))

    f.VotesFactory.create(content_object=issue, count=5)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['total_voters'] == 5


def test_get_issue_is_voted(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    f.MembershipFactory.create(project=issue.project, user=user, is_admin=True)
    f.VotesFactory.create(content_object=issue)
    url_detail = reverse("issues-detail", args=(issue.id,))
    url_upvote = reverse("issues-upvote", args=(issue.id,))
    url_downvote = reverse("issues-downvote", args=(issue.id,))

    client.login(user)

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_voters'] == 0
    assert response.data['is_voter'] == False

    response = client.post(url_upvote)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_voters'] == 1
    assert response.data['is_voter'] == True

    response = client.post(url_downvote)
    assert response.status_code == 200

    response = client.get(url_detail)
    assert response.status_code == 200
    assert response.data['total_voters'] == 0
    assert response.data['is_voter'] == False
