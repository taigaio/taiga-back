import pytest

from django.core.urlresolvers import reverse
from .. import factories

pytestmark = pytest.mark.django_db


@pytest.fixture
def register_form():
    return {"username": "username",
            "password": "password",
            "full_name": "fname",
            "email": "user@email.com",
            "type": "public"}


def test_respond_201_if_domain_allows_public_registration(client, register_form):
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201


def test_respond_400_if_domain_does_not_allow_public_registration(client, register_form):
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_respond_201_if_domain_allows_public_registration(client, register_form):
    user = factories.UserFactory()
    membership = factories.MembershipFactory(user=user)

    register_form.update({
        "type": "private",
        "existing": "1",
        "token": membership.token,
        "username": user.username,
        "email": user.email,
        "password": user.username,
    })

    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201
