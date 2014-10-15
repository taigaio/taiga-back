import pytest
import json
from tempfile import NamedTemporaryFile

from django.core.urlresolvers import reverse

from .. import factories as f

from taiga.users import models
from taiga.auth.tokens import get_token_for_user

pytestmark = pytest.mark.django_db


def test_users_create_through_standard_api(client):
    user = f.UserFactory.create(is_superuser=True)

    url = reverse('users-list')
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 405

    client.login(user)

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 405


def test_update_user_with_same_email(client):
    user = f.UserFactory.create(email="same@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "same@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_update_user_with_duplicated_email(client):
    f.UserFactory.create(email="one@email.com")
    user = f.UserFactory.create(email="two@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "one@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Duplicated email'


def test_update_user_with_invalid_email(client):
    user = f.UserFactory.create(email="my@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "my@email"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400
    assert response.data['_error_message'] == 'Not valid email'


def test_update_user_with_valid_email(client):
    user = f.UserFactory.create(email="old@email.com")
    url = reverse('users-detail', kwargs={"pk": user.pk})
    data = {"email": "new@email.com"}

    client.login(user)
    response = client.patch(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 200
    user = models.User.objects.get(pk=user.id)
    assert  user.email_token != None
    assert  user.new_email == "new@email.com"


def test_validate_requested_email_change(client):
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


def test_validate_requested_email_change_without_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400


def test_validate_requested_email_change_with_invalid_token(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "invalid_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400


def test_delete_self_user(client):
    user = f.UserFactory.create()
    url = reverse('users-detail', kwargs={"pk": user.pk})

    client.login(user)
    response = client.delete(url)

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.full_name == "Deleted user"


def test_cancel_self_user_with_valid_token(client):
    user = f.UserFactory.create()
    url = reverse('users-cancel')
    cancel_token = get_token_for_user(user, "cancel_account")
    data = {"cancel_token": cancel_token}
    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.full_name == "Deleted user"


def test_cancel_self_user_with_invalid_token(client):
    user = f.UserFactory.create()
    url = reverse('users-cancel')
    data = {"cancel_token": "invalid_cancel_token"}
    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 400


DUMMY_BMP_DATA = b'BM:\x00\x00\x00\x00\x00\x00\x006\x00\x00\x00(\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00\x00\x00\x00\x00\x04\x00\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def test_change_avatar(client):
    url = reverse('users-change-avatar')

    user = f.UserFactory()
    client.login(user)

    with NamedTemporaryFile() as avatar:
        # Test no avatar send
        post_data = {}
        response = client.post(url, post_data)
        assert response.status_code == 400

        # Test invalid file send
        post_data = {
            'avatar': avatar
        }
        response = client.post(url, post_data)
        assert response.status_code == 400

        # Test empty valid avatar send
        avatar.write(DUMMY_BMP_DATA)
        avatar.seek(0)
        response = client.post(url, post_data)
        assert response.status_code == 200
