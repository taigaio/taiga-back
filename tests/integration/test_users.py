import pytest
import json

from django.core.urlresolvers import reverse

from .. import factories as f

from taiga.users import models

pytestmark = pytest.mark.django_db


def test_api_user_patch_same_email(client):
    user = f.UserFactory.create(email="same@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "same@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_api_user_patch_duplicated_email(client):
    f.UserFactory.create(email="one@email.com")
    user = f.UserFactory.create(email="two@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "one@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_api_user_patch_invalid_email(client):
    user = f.UserFactory.create(email="my@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "my@email"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Not valid email'


def test_api_user_patch_valid_email(client):
    user = f.UserFactory.create(email="old@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "new@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    user = models.User.objects.get(pk=user.id)
    assert  user.email_token != None
    assert  user.new_email == "new@email.com"


def test_api_user_action_change_email_ok(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "change_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert  user.email_token == None
    assert  user.new_email == None
    assert  user.email == "new@email.com"


def test_api_user_action_change_email_no_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Invalid, are you sure the token is correct and you didn\'t use it before?'


def test_api_user_action_change_email_invalid_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "invalid_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Invalid, are you sure the token is correct and you didn\'t use it before?'
