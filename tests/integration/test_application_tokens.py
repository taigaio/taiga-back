from django.core.urlresolvers import reverse

from taiga.external_apps import encryption
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
    decyphered_token = encryption.decrypt(response.data["cyphered_token"], token.application.key)[0]
    decyphered_token = json.loads(decyphered_token.decode("utf-8"))
    assert decyphered_token["token"] == token.token
