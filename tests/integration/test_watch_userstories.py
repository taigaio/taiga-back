# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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
from django.core.urlresolvers import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_watch_user_story(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    url = reverse("userstories-watch", args=(user_story.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_unwatch_user_story(client):
    user = f.UserFactory.create()
    user_story = f.create_userstory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    url = reverse("userstories-unwatch", args=(user_story.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_user_story_watchers(client):
    user = f.UserFactory.create()
    user_story = f.UserStoryFactory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    f.WatchedFactory.create(content_object=user_story, user=user)
    url = reverse("userstory-watchers-list", args=(user_story.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_user_story_watcher(client):
    user = f.UserFactory.create()
    user_story = f.UserStoryFactory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    watch = f.WatchedFactory.create(content_object=user_story, user=user)
    url = reverse("userstory-watchers-detail", args=(user_story.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id


def test_get_user_story_watchers(client):
    user = f.UserFactory.create()
    user_story = f.UserStoryFactory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    url = reverse("userstories-detail", args=(user_story.id,))

    f.WatchedFactory.create(content_object=user_story, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['watchers'] == [user.id]
    assert response.data['total_watchers'] == 1


def test_get_user_story_is_watcher(client):
    user = f.UserFactory.create()
    user_story = f.UserStoryFactory(owner=user)
    f.MembershipFactory.create(project=user_story.project, user=user, is_owner=True)
    url_detail = reverse("userstories-detail", args=(user_story.id,))
    url_watch = reverse("userstories-watch", args=(user_story.id,))
    url_unwatch = reverse("userstories-unwatch", args=(user_story.id,))

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


def test_remove_user_story_watcher(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    us = f.UserStoryFactory(project=project,
                           status__project=project,
                           milestone__project=project)

    us.add_watcher(user)
    role = f.RoleFactory.create(project=project, permissions=['modify_us', 'view_us'])
    f.MembershipFactory.create(project=project, user=user, role=role)

    url = reverse("userstories-detail", args=(us.id,))

    client.login(user)

    data = {"version": us.version, "watchers": []}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data['watchers'] == []
    assert response.data['is_watcher'] == False
