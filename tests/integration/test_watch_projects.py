# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Anler Hernández <hello@anler.me>
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

from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_watch_project(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-watch", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_watch_project_with_valid_notify_level(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-watch", args=(project.id,))

    client.login(user)
    data = {
        "notify_level": 1
    }
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200


def test_watch_project_with_invalid_notify_level(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-watch", args=(project.id,))

    client.login(user)
    data = {
        "notify_level": 333
    }
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert response.data["_error_message"] == "Invalid value for notify level"


def test_unwatch_project(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-unwatch", args=(project.id,))

    client.login(user)
    response = client.post(url)

    assert response.status_code == 200


def test_list_project_watchers(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    f.WatchedFactory.create(content_object=project, user=user)
    url = reverse("project-watchers-list", args=(project.id,))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data[0]['id'] == user.id


def test_get_project_watcher(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    watch = f.WatchedFactory.create(content_object=project, user=user)
    url = reverse("project-watchers-detail", args=(project.id, watch.user.id))

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == watch.user.id


def test_get_project_watchers(client):
    user = f.UserFactory.create()
    project = f.create_project(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("projects-detail", args=(project.id,))

    f.WatchedFactory.create(content_object=project, user=user)

    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.data['total_watchers'] == 1


def test_get_project_is_watcher(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=False,
            anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
            public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)))

    url_detail = reverse("projects-detail", args=(project.id,))
    url_watch = reverse("projects-watch", args=(project.id,))
    url_unwatch = reverse("projects-unwatch", args=(project.id,))

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
