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


def test_upvote_user_story(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user, status=None)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    url = reverse("userstories-upvote", args=(user_story.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_downvote_user_story(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user, status=None)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    url = reverse("userstories-downvote", args=(user_story.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_user_story_voters(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    f.VoteFactory.create(content_object=user_story, user=user)
    url = reverse("userstory-voters-list", args=(user_story.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id

def test_get_userstory_voter(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    vote = f.VoteFactory.create(content_object=user_story, user=user)
    url = reverse("userstory-voters-detail", args=(user_story.id, vote.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == vote.user.id


def test_get_user_story_votes(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    url = reverse("userstories-detail", args=(user_story.id,))

    f.VotesFactory.create(content_object=user_story, count=5)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['total_voters'] == 5


def test_get_user_story_is_voted(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user, status=None)
    f.MembershipFactory.create(project=user_story.project, user=user, is_admin=True)
    f.VotesFactory.create(content_object=user_story)
    url_detail = reverse("userstories-detail", args=(user_story.id,))
    url_upvote = reverse("userstories-upvote", args=(user_story.id,))
    url_downvote = reverse("userstories-downvote", args=(user_story.id,))

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
