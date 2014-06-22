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
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_upvote_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    url = reverse("issues-upvote", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_downvote_issue(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    url = reverse("issues-downvote", args=(issue.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_issue_voters(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    url = reverse("issue-voters-list", args=(issue.id,))
    f.VoteFactory.create(content_object=issue, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_issue_voter(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    vote = f.VoteFactory.create(content_object=issue, user=user)
    url = reverse("issue-voters-detail", args=(issue.id, vote.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == vote.user.id


def test_get_issue_votes(client):
    user = f.UserFactory.create()
    issue = f.create_issue(owner=user)
    url = reverse("issues-detail", args=(issue.id,))
    f.VotesFactory.create(content_object=issue, count=5)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['votes'] == 5
