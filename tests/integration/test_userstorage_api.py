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

from django.core.urlresolvers import reverse
from .. import factories

from taiga.base.utils import json

pytestmark = pytest.mark.django_db


def test_list_userstorage(client):
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    storage11 = factories.StorageEntryFactory(owner=user1)
    factories.StorageEntryFactory(owner=user1)
    storage13 = factories.StorageEntryFactory(owner=user1)
    factories.StorageEntryFactory(owner=user2)

    # List by anonumous user
    response = client.json.get(reverse("user-storage-list"))
    assert response.status_code == 200
    assert len(response.data) == 0

    # List own entries
    client.login(username=user1.username, password=user1.username)
    response = client.json.get(reverse("user-storage-list"))
    assert response.status_code == 200
    assert len(response.data) == 3

    client.login(username=user2.username, password=user2.username)
    response = client.json.get(reverse("user-storage-list"))
    assert response.status_code == 200
    assert len(response.data) == 1

    # Filter results by key
    client.login(username=user1.username, password=user1.username)
    keys = ",".join([storage11.key, storage13.key])
    url = "{}?keys={}".format(reverse("user-storage-list"), keys)

    response = client.json.get(url)
    assert response.status_code == 200
    assert len(response.data) == 2


def test_view_storage_entries(client):
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    storage11 = factories.StorageEntryFactory(owner=user1)

    # Get by anonymous user
    response = client.json.get(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 404

    # Get single entry
    client.login(username=user1.username, password=user1.username)
    response = client.json.get(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 200
    assert response.data["key"] == storage11.key
    assert response.data["value"] == storage11.value

    # Get not existent key
    client.login(username=user2.username, password=user2.username)
    response = client.json.get(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 404

    response = client.json.get(reverse("user-storage-detail", args=["foobar"]))
    assert response.status_code == 404


def test_create_entries(client):
    user1 = factories.UserFactory()
    storage11 = factories.StorageEntryFactory(owner=user1)

    form = {"key": "foo",
            "value": {"bar": "bar"}}
    form_without_key = {"value": {"bar": "bar"}}
    form_without_value = {"key": "foo"}
    error_form = {"key": storage11.key,
                  "value": {"bar": "bar"}}

    # Create entry by anonymous user
    response = client.json.post(reverse("user-storage-list"), json.dumps(form))
    assert response.status_code == 401

    # Create by logged user
    client.login(username=user1.username, password=user1.username)
    response = client.json.post(reverse("user-storage-list"), json.dumps(form))
    assert response.status_code == 201
    response = client.json.get(reverse("user-storage-detail", args=[form["key"]]))
    assert response.status_code == 200

    # Wrong data
    client.login(username=user1.username, password=user1.username)
    response = client.json.post(reverse("user-storage-list"), json.dumps(form_without_key))
    assert response.status_code == 400
    response = client.json.post(reverse("user-storage-list"), json.dumps(form_without_value))
    assert response.status_code == 400
    response = client.json.post(reverse("user-storage-list"), json.dumps(error_form))
    assert response.status_code == 400


def test_update_entries(client):
    user1 = factories.UserFactory()
    storage11 = factories.StorageEntryFactory(owner=user1)

    # Update by anonymous user
    form = {"value": "bar", "key": storage11.key}
    response = client.json.put(reverse("user-storage-detail", args=[storage11.key]),
                               json.dumps(form))
    assert response.status_code == 401

    # Update by logged user
    client.login(username=user1.username, password=user1.username)
    form = {"value": {"bar": "bar"}, "key": storage11.key}

    response = client.json.put(reverse("user-storage-detail", args=[storage11.key]),
                               json.dumps(form))
    assert response.status_code == 200
    response = client.json.get(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 200
    assert response.data["value"] == form["value"]

    # Update not existing entry
    form = {"value": {"bar": "bar"}, "key": "foo"}
    response = client.json.get(reverse("user-storage-detail", args=[form["key"]]))
    assert response.status_code == 404
    response = client.json.put(reverse("user-storage-detail", args=[form["key"]]),
                               json.dumps(form))
    assert response.status_code == 201
    response = client.json.get(reverse("user-storage-detail", args=[form["key"]]))
    assert response.status_code == 200
    assert response.data["value"] == form["value"]


def test_delete_storage_entry(client):
    user1 = factories.UserFactory()
    user2 = factories.UserFactory()
    storage11 = factories.StorageEntryFactory(owner=user1)

    # Delete by anonumous user
    response = client.json.delete(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 401

    # Delete by logged user
    client.login(username=user1.username, password=user1.username)
    response = client.json.delete(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 204

    response = client.json.get(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 404

    # Delete not existent entry
    response = client.json.delete(reverse("user-storage-detail", args=["foo"]))
    assert response.status_code == 404

    client.login(username=user2.username, password=user2.username)
    response = client.json.delete(reverse("user-storage-detail", args=[storage11.key]))
    assert response.status_code == 404
