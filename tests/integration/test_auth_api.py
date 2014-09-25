# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
from unittest.mock import patch, Mock

from django.apps import apps
from django.core.urlresolvers import reverse
from .. import factories

from taiga.base.connectors import github


pytestmark = pytest.mark.django_db


@pytest.fixture
def register_form():
    return {"username": "username",
            "password": "password",
            "full_name": "fname",
            "email": "user@email.com",
            "type": "public"}


def test_respond_201_if_domain_allows_public_registration(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201


def test_respond_400_if_domain_does_not_allow_public_registration(client, register_form):
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_respond_201_with_invitation_if_domain_does_not_allows_public_registration(client, register_form):
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

    assert response.status_code == 201, response.data


def test_response_200_in_registration_with_github_account(client):
    form = {"type": "github",
            "code": "xxxxxx"}

    with patch("taiga.base.connectors.github.me") as m_me:
        m_me.return_value = ("mmcfly@bttf.com",
                             github.User(id=1955,
                                        username="mmcfly",
                                        full_name="martin seamus mcfly",
                                        bio="time traveler"))

        response = client.post(reverse("auth-list"), form)
        assert response.status_code == 200
        assert response.data["username"] == "mmcfly"
        assert response.data["auth_token"] != "" and response.data["auth_token"] != None
        assert response.data["email"] == "mmcfly@bttf.com"
        assert response.data["full_name"] == "martin seamus mcfly"
        assert response.data["bio"] == "time traveler"
        assert response.data["github_id"] == 1955


def test_response_200_in_registration_with_github_account_in_a_project(client):
    membership_model = apps.get_model("projects", "Membership")
    membership = factories.MembershipFactory(user=None)
    form = {"type": "github",
            "code": "xxxxxx",
            "token": membership.token}

    with patch("taiga.base.connectors.github.me") as m_me:
        m_me.return_value = ("mmcfly@bttf.com",
                             github.User(id=1955,
                                        username="mmcfly",
                                        full_name="martin seamus mcfly",
                                        bio="time traveler"))

        response = client.post(reverse("auth-list"), form)
        assert response.status_code == 200
        assert membership_model.objects.get(token=form["token"]).user.username == "mmcfly"


def test_response_404_in_registration_with_github_account_in_a_project_with_invalid_token(client):
    form = {"type": "github",
            "code": "xxxxxx",
            "token": "123456"}

    with patch("taiga.base.connectors.github.me") as m_me:
        m_me.return_value = ("mmcfly@bttf.com",
                             github.User(id=1955,
                                        username="mmcfly",
                                        full_name="martin seamus mcfly",
                                        bio="time traveler"))

        response = client.post(reverse("auth-list"), form)
        assert response.status_code == 404


def test_respond_400_If_username_is_invalid(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True

    register_form.update({"username": "User Examp:/e"})
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    register_form.update({"username": 300*"a"})
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400
