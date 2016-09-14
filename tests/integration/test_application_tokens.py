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

from taiga.external_apps import models


from .. import factories as f

import json
import pytest
pytestmark = pytest.mark.django_db


def test_own_tokens_listing(client):
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    token_1 = f.ApplicationTokenFactory(user=user_1)
    token_2 = f.ApplicationTokenFactory(user=user_2)
    url = reverse("application-tokens-list")
    client.login(user_1)
    response = client.json.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0].get("id") ==  token_1.id
    assert response.data[0].get("application").get("id") ==  token_1.application.id


def test_retrieve_existing_token_for_application(client):
    token = f.ApplicationTokenFactory()
    url = reverse("applications-token", args=[token.application.id])
    client.login(token.user)
    response = client.json.get(url)
    assert response.status_code == 200
    assert response.data.get("application").get("id") == token.application.id



def test_retrieve_unexisting_token_for_application(client):
    user = f.UserFactory.create()
    url = reverse("applications-token", args=[-1])
    client.login(user)
    response = client.json.get(url)
    assert response.status_code == 404


def test_token_authorize(client):
    user = f.UserFactory.create()
    application = f.ApplicationFactory()
    url = reverse("application-tokens-authorize")
    client.login(user)

    data = json.dumps({
            "application": application.id,
            "state": "random-state"
    })

    response = client.json.post(url, data)

    assert response.status_code == 200
    assert response.data["state"] == "random-state"
    auth_code_1 = response.data["auth_code"]

    response = client.json.post(url, data)
    assert response.status_code == 200
    assert response.data["state"] == "random-state"
    auth_code_2 = response.data["auth_code"]
    assert auth_code_1 != auth_code_2


def test_token_authorize_invalid_app(client):
    user = f.UserFactory.create()
    url = reverse("application-tokens-authorize")
    client.login(user)

    data = json.dumps({
            "application": 33,
            "state": "random-state"
    })

    response = client.json.post(url, data)
    assert response.status_code == 404


def test_token_validate(client):
    user = f.UserFactory.create()
    application = f.ApplicationFactory(next_url="http://next.url")
    token = f.ApplicationTokenFactory(auth_code="test-auth-code", state="test-state", application=application)
    url = reverse("application-tokens-validate")
    client.login(user)

    data = {
        "application": token.application.id,
        "auth_code": "test-auth-code",
        "state": "test-state"
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200

    token = models.ApplicationToken.objects.get(id=token.id)
    assert response.data["token"] == token.token


def test_token_validate_validated(client):
    # Validating a validated token should update the token attribute
    user = f.UserFactory.create()
    application = f.ApplicationFactory(next_url="http://next.url")
    token = f.ApplicationTokenFactory(
        auth_code="test-auth-code",
        state="test-state",
        application=application,
        token="existing-token")

    url = reverse("application-tokens-validate")
    client.login(user)

    data = {
        "application": token.application.id,
        "auth_code": "test-auth-code",
        "state": "test-state"
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200

    token = models.ApplicationToken.objects.get(id=token.id)
    assert token.token == "existing-token"
