# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from tempfile import NamedTemporaryFile

from django.urls import reverse

from taiga.base.utils import json
from taiga.users.serializers import UserAdminSerializer

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

import pytest
pytestmark = pytest.mark.django_db

DUMMY_BMP_DATA = b'BM:\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.other_user = f.UserFactory.create()
    m.superuser = f.UserFactory.create(is_superuser=True)

    return m


def test_user_retrieve(client, data):
    url = reverse('users-detail', kwargs={"pk": data.registered_user.pk})

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200, 200]


def test_user_me(client, data):
    url = reverse('users-me')

    users = [
        None,
        data.registered_user
    ]

    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [401, 200]


def test_user_by_username(client, data):
    url = reverse('users-by-username')

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'get', "{}?username={}".format(url, data.registered_user.username), None, users)
    assert results == [200, 200, 200, 200]


def test_user_update(client, data):
    url = reverse('users-detail', kwargs={"pk": data.registered_user.pk})

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    user_data = UserAdminSerializer(data.registered_user).data
    user_data["full_name"] = "test"
    user_data = json.dumps(user_data)

    results = helper_test_http_method(client, 'put', url, user_data, users)
    assert results == [401, 200, 403, 200]


def test_user_delete(client, data):
    url = reverse('users-detail', kwargs={"pk": data.registered_user.pk})

    users = [
        None,
        data.other_user,
        data.registered_user,
    ]

    results = helper_test_http_method(client, 'delete', url, None, users)
    assert results == [401, 404, 204]


def test_user_list(client, data):
    url = reverse('users-list')

    response = client.get(url)
    users_data = json.loads(response.content.decode('utf-8'))
    assert len(users_data) == 0
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    users_data = json.loads(response.content.decode('utf-8'))
    assert len(users_data) == 1
    assert response.status_code == 200

    client.login(data.other_user)

    response = client.get(url)
    users_data = json.loads(response.content.decode('utf-8'))
    assert len(users_data) == 1
    assert response.status_code == 200

    client.login(data.superuser)

    response = client.get(url)
    users_data = json.loads(response.content.decode('utf-8'))
    assert len(users_data) == 3
    assert response.status_code == 200


def test_user_create(client, data):
    url = reverse('users-list')

    users = [
        None,
    ]

    create_data = json.dumps({
        "username": "test",
        "full_name": "test",
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [405]


def test_user_patch(client, data):
    url = reverse('users-detail', kwargs={"pk": data.registered_user.pk})

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    patch_data = json.dumps({"full_name": "test"})
    results = helper_test_http_method(client, 'patch', url, patch_data, users)
    assert results == [401, 200, 404, 200]


def test_user_action_change_password(client, data):
    url = reverse('users-change-password')

    data.registered_user.set_password("test-current-password")
    data.registered_user.save()
    data.other_user.set_password("test-current-password")
    data.other_user.save()
    data.superuser.set_password("test-current-password")
    data.superuser.save()

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    post_data = json.dumps({"current_password": "test-current-password", "password": "test-password"})
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 204, 204, 204]


def test_user_action_change_avatar(client, data):
    url = reverse('users-change-avatar')

    with NamedTemporaryFile() as avatar:
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)

        post_data = {
            'avatar': avatar
        }

        client.logout()
        response = client.post(url, post_data)
        assert response.status_code == 401

        avatar.seek(0)
        client.login(data.registered_user)
        response = client.post(url, post_data)
        assert response.status_code == 200

        avatar.seek(0)
        client.login(data.other_user)
        response = client.post(url, post_data)
        assert response.status_code == 200

        avatar.seek(0)
        client.login(data.superuser)
        response = client.post(url, post_data)
        assert response.status_code == 200


def test_user_action_remove_avatar(client, data):
    url = reverse('users-remove-avatar')

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'post', url, None, users)
    assert results == [401, 200, 200, 200]


def test_user_action_change_password_from_recovery(client, data):
    url = reverse('users-change-password-from-recovery')

    new_user = f.UserFactory(token="test-token")

    def reset_token():
        new_user.token = "test-token"
        new_user.save()

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    patch_data = json.dumps({"password": "test-password", "token": "test-token"})
    results = helper_test_http_method(client, 'post', url, patch_data, users, reset_token)
    assert results == [204, 204, 204, 204]


def test_user_action_password_recovery(client, data):
    url = reverse('users-password-recovery')

    f.UserFactory.create(username="test")

    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]

    patch_data = json.dumps({"username": "test"})
    results = helper_test_http_method(client, 'post', url, patch_data, users)
    assert results == [200, 200, 200, 200]


def test_user_action_change_email(client, data):
    url = reverse('users-change-email')

    def after_each_request():
        data.registered_user.email_token = "test-token"
        data.registered_user.new_email = "new@email.com"
        data.registered_user.save()

    users = [
        None,
        data.registered_user,
        data.other_user,
    ]

    patch_data = json.dumps({"email_token": "test-token"})
    after_each_request()
    results = helper_test_http_method(client, 'post', url, patch_data, users, after_each_request=after_each_request)
    assert results == [204, 204, 204]


def test_user_list_watched(client, data):
    url = reverse('users-watched', kwargs={"pk": data.registered_user.pk})
    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]
    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200, 200]


def test_user_list_liked(client, data):
    url = reverse('users-liked', kwargs={"pk": data.registered_user.pk})
    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]
    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200, 200]


def test_user_list_voted(client, data):
    url = reverse('users-voted', kwargs={"pk": data.registered_user.pk})
    users = [
        None,
        data.registered_user,
        data.other_user,
        data.superuser,
    ]
    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200, 200]
