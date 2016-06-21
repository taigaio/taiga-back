# -*- coding: utf-8 -*-
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

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.userstorage.serializers import StorageEntrySerializer
from taiga.userstorage.models import StorageEntry

from tests import factories as f
from tests.utils import helper_test_http_method
from tests.utils import helper_test_http_method_and_count
from tests.utils import disconnect_signals, reconnect_signals

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.user1 = f.UserFactory.create()
    m.user2 = f.UserFactory.create()

    m.storage_user1 = f.StorageEntryFactory(owner=m.user1)
    m.storage_user2 = f.StorageEntryFactory(owner=m.user2)
    m.storage2_user2 = f.StorageEntryFactory(owner=m.user2)

    return m


def test_storage_retrieve(client, data):
    url = reverse('user-storage-detail', kwargs={"key": data.storage_user1.key})

    users = [
        None,
        data.user1,
        data.user2,
    ]

    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [404, 200, 404]


def test_storage_update(client, data):
    url = reverse('user-storage-detail', kwargs={"key": data.storage_user1.key})

    users = [
        None,
        data.user1,
        data.user2,
    ]

    storage_data = StorageEntrySerializer(data.storage_user1).data
    storage_data["key"] = "test"
    storage_data = json.dumps(storage_data)
    results = helper_test_http_method(client, 'put', url, storage_data, users)
    assert results == [401, 200, 404]


def test_storage_delete(client, data):
    url = reverse('user-storage-detail', kwargs={"key": data.storage_user1.key})

    users = [
        None,
        data.user1,
        data.user2,
    ]

    results = helper_test_http_method(client, 'delete', url, None, users)
    assert results == [401, 204, 404]


def test_storage_list(client, data):
    url = reverse('user-storage-list')

    users = [
        None,
        data.user1,
        data.user2,
    ]

    results = helper_test_http_method_and_count(client, 'get', url, None, users)
    assert results == [(200, 0), (200, 1), (200, 2)]


def test_storage_create(client, data):
    url = reverse('user-storage-list')

    users = [
        None,
        data.user1,
        data.user2,
    ]

    create_data = json.dumps({
        "key": "test",
        "value": {"test": "test-value"},
    })
    results = helper_test_http_method(client, 'post', url, create_data, users, lambda: StorageEntry.objects.all().delete())
    assert results == [401, 201, 201]


def test_storage_patch(client, data):
    url = reverse('user-storage-detail', kwargs={"key": data.storage_user1.key})

    users = [
        None,
        data.user1,
        data.user2,
    ]

    patch_data = json.dumps({"value": {"test": "test-value"}})
    results = helper_test_http_method(client, 'patch', url, patch_data, users)
    assert results == [401, 200, 404]
