import pytest
from tempfile import NamedTemporaryFile

from django.core.urlresolvers import reverse

from .. import factories as f

from taiga.base.utils import json
from taiga.users import models
from taiga.auth.tokens import get_token_for_user
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

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
    assert user.email_token is not None
    assert user.new_email == "new@email.com"


def test_validate_requested_email_change(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "change_email_token"}

    client.login(user)
    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is None
    assert user.new_email is None
    assert user.email == "new@email.com"

def test_validate_requested_email_change_for_anonymous_user(client):
    user = f.UserFactory.create(email_token="change_email_token", new_email="new@email.com")
    url = reverse('users-change-email')
    data = {"email_token": "change_email_token"}

    response = client.post(url, json.dumps(data), content_type="application/json")

    assert response.status_code == 204
    user = models.User.objects.get(pk=user.id)
    assert user.email_token is None
    assert user.new_email is None
    assert user.email == "new@email.com"

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


def test_list_contacts_private_projects(client):
    project = f.ProjectFactory.create()
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role = f.RoleFactory(project=project, permissions=["view_project"])
    membership_1 = f.MembershipFactory.create(project=project, user=user_1, role=role)
    membership_2 = f.MembershipFactory.create(project=project, user=user_2, role=role)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_content = json.loads(response.content.decode("utf-8"))
    assert len(response_content) == 0

    client.login(user_1)
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_content = json.loads(response.content.decode("utf-8"))
    assert len(response_content) == 1
    assert response_content[0]["id"] == user_2.id


def test_list_contacts_no_projects(client):
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role_1 = f.RoleFactory(permissions=["view_project"])
    role_2 = f.RoleFactory(permissions=["view_project"])
    membership_1 = f.MembershipFactory.create(project=role_1.project, user=user_1, role=role_1)
    membership_2 = f.MembershipFactory.create(project=role_2.project, user=user_2, role=role_2)

    client.login(user_1)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200

    response_content = json.loads(response.content.decode("utf-8"))
    assert len(response_content) == 0


def test_list_contacts_public_projects(client):
    project = f.ProjectFactory.create(is_private=False,
            anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
            public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)))

    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    role = f.RoleFactory(project=project)
    membership_1 = f.MembershipFactory.create(project=project, user=user_1, role=role)
    membership_2 = f.MembershipFactory.create(project=project, user=user_2, role=role)

    url = reverse('users-contacts', kwargs={"pk": user_1.pk})
    response = client.get(url, content_type="application/json")
    assert response.status_code == 200

    response_content = json.loads(response.content.decode("utf-8"))
    assert len(response_content) == 1
    assert response_content[0]["id"] == user_2.id
