# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import datetime

import pytest

from django.urls import reverse
from django.core import mail
from django.utils import timezone

from .. import factories

pytestmark = pytest.mark.django_db


@pytest.fixture
def register_form():
    return {"username": "username",
            "password": "password",
            "full_name": "fname",
            "email": "user@email.com",
            "accepted_terms": True,
            "type": "public"}


@pytest.fixture
def isolated_auth_throttle_cache(settings, request):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": request.node.nodeid,
        }
    }
    settings.AUTH_THROTTLE_TRUSTED_PROXIES = []

#################
# registration
#################

def test_respond_201_when_public_registration_is_enabled(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201


@pytest.mark.parametrize(("password_length", "status_code"), [(128, 201), (129, 400)])
def test_register_password_max_length(client, settings, register_form, password_length, status_code):
    settings.PUBLIC_REGISTER_ENABLED = True
    register_form["password"] = "p" * password_length

    response = client.post(reverse("auth-register"), register_form)

    assert response.status_code == status_code
    if status_code == 400:
        assert "password" in response.data


def test_respond_400_when_public_registration_is_disabled(client, register_form, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_respond_400_when_the_email_domain_isnt_in_allowed_domains(client, register_form, settings):
    settings.PUBLIC_REGISTER_ENABLED = True
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['other-domain.com']
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_respond_201_when_the_email_domain_is_in_allowed_domains(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True
    settings.USER_EMAIL_ALLOWED_DOMAINS = ['email.com']
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201


def test_response_200_in_public_registration(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = True
    form = {
        "type": "public",
        "username": "mmcfly",
        "full_name": "martin seamus mcfly",
        "email": "mmcfly@bttf.com",
        "password": "password",
        "accepted_terms": True,
    }

    response = client.post(reverse("auth-register"), form)
    assert response.status_code == 201
    assert response.data["username"] == "mmcfly"
    assert response.data["email"] == "mmcfly@bttf.com"
    assert response.data["full_name"] == "martin seamus mcfly"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "You've been Taigatized!"


def test_respond_400_if_username_is_invalid(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True

    register_form.update({"username": "User Examp:/e"})
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    register_form.update({"username": 300*"a"})
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_respond_400_if_username_or_email_is_duplicate(client, settings, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True

    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201

    register_form["username"] = "username"
    register_form["email"] = "ff@dd.com"
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


def test_register_success_throttling(client, settings, monkeypatch, isolated_auth_throttle_cache):
    settings.PUBLIC_REGISTER_ENABLED = True
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "register-success", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", ["127.0.0.1"])

    register_form = {"username": "valid_username_register_success",
                     "password": "valid_password",
                     "full_name": "fullname",
                     "email": "",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    register_form = {"username": "valid_username_register_success",
                     "password": "valid_password",
                     "full_name": "fullname",
                     "email": "valid_username_register_success@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201

    register_form = {"username": "valid_username_register_success2",
                     "password": "valid_password2",
                     "full_name": "fullname",
                     "email": "valid_username_register_success2@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 429

    register_form = {"username": "valid_username_register_success2",
                     "password": "valid_password2",
                     "full_name": "fullname",
                     "email": "",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 429



INVALID_NAMES = [
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod",
    "an <script>evil()</script> example",
    "http://testdomain.com",
    "https://testdomain.com",
    "Visit http://testdomain.com",
]

@pytest.mark.parametrize("full_name", INVALID_NAMES)
def test_register_sanitize_invalid_user_full_name(client, settings, full_name, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True
    register_form["full_name"] = full_name
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

VALID_NAMES = [
    "martin seamus mcfly"
]

@pytest.mark.parametrize("full_name", VALID_NAMES)
def test_register_sanitize_valid_user_full_name(client, settings, full_name, register_form):
    settings.PUBLIC_REGISTER_ENABLED = True
    register_form["full_name"] = full_name
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201


def test_registration_case_insensitive_for_username_and_password(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = True

    register_form = {"username": "Username",
                     "password": "password",
                     "full_name": "fname",
                     "email": "User@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201

    # Email is case insensitive in the register process
    register_form = {"username": "username2",
                     "password": "password",
                     "full_name": "fname",
                     "email": "user@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    # Username is case insensitive in the register process too
    register_form = {"username": "username",
                     "password": "password",
                     "full_name": "fname",
                     "email": "user2@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400


#################
# autehtication
#################

def test_get_auth_token_with_username(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 200, response.data
    assert "auth_token" in response.data and response.data["auth_token"]
    assert "refresh" in response.data and response.data["refresh"]


def test_get_auth_token_with_username_case_insensitive(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()

    auth_data = {
        "username": user.username.upper(),
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 200, response.data
    assert "auth_token" in response.data and response.data["auth_token"]
    assert "refresh" in response.data and response.data["refresh"]


def test_get_auth_token_with_email(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()

    auth_data = {
        "username": user.email,
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 200, response.data
    assert "auth_token" in response.data and response.data["auth_token"]
    assert "refresh" in response.data and response.data["refresh"]


def test_get_auth_token_with_email_case_insensitive(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()

    auth_data = {
        "username": user.email.upper(),
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 200, response.data
    assert "auth_token" in response.data and response.data["auth_token"]
    assert "refresh" in response.data and response.data["refresh"]


def test_get_auth_token_with_project_invitation(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()
    membership = factories.MembershipFactory(user=None)

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
        "invitation_token": membership.token,
    }

    assert membership.user == None

    response = client.post(reverse("auth-list"), auth_data)
    membership.refresh_from_db()

    assert response.status_code == 200, response.data
    assert "auth_token" in response.data and response.data["auth_token"]
    assert "refresh" in response.data and response.data["refresh"]
    assert membership.user == user


def test_get_auth_token_with_expired_project_invitation(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()
    membership = factories.MembershipFactory(
        user=None,
        token_expires_at=timezone.now() - datetime.timedelta(days=1),
    )

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
        "invitation_token": membership.token,
    }

    response = client.post(reverse("auth-list"), auth_data)
    membership.refresh_from_db()

    assert response.status_code == 404, response.data
    assert membership.user == None


def test_reuse_accepted_invitation_token_is_rejected(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()
    membership = factories.MembershipFactory(user=None)

    # The invited user accepts the invitation
    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
        "invitation_token": membership.token,
    }
    response = client.post(reverse("auth-list"), auth_data)
    assert response.status_code == 200, response.data

    # The invitation token can not be reused to assign the
    # membership to a different user
    attacker = factories.UserFactory()
    auth_data = {
        "username": attacker.username,
        "password": attacker.username,
        "type": "normal",
        "invitation_token": membership.token,
    }
    response = client.post(reverse("auth-list"), auth_data)
    membership.refresh_from_db()

    assert response.status_code == 404, response.data
    assert membership.user == user


def test_get_auth_token_error_invalid_credentials(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory()

    auth_data = {
        "username": "bad username",
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 401, response.data

    auth_data = {
        "username": user.username,
        "password": "invalid password",
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 401, response.data


def test_get_auth_token_error_inactive_user(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory(is_active=False)

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 401, response.data


def test_get_auth_token_error_inactive_user(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory(is_active=False)

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 401, response.data

def test_get_auth_token_error_system_user(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = False
    user = factories.UserFactory(is_system=True)

    auth_data = {
        "username": user.username,
        "password": user.username,
        "type": "normal",
    }

    response = client.post(reverse("auth-list"), auth_data)

    assert response.status_code == 401, response.data


def test_auth_uppercase_ignore(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = True

    register_form = {"username": "Username",
                     "password": "password",
                     "full_name": "fname",
                     "email": "User@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 201

    #Only exists one user with the same lowercase version of username/password
    login_form = {"type": "normal",
                  "username": "Username",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 200

    login_form = {"type": "normal",
                  "username": "User@email.com",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 200

    # Email is case insensitive in the register process
    register_form = {"username": "username2",
                     "password": "password",
                     "full_name": "fname",
                     "email": "user@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    # Username is case insensitive in the register process too
    register_form = {"username": "username",
                     "password": "password",
                     "full_name": "fname",
                     "email": "user2@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)
    assert response.status_code == 400

    #Now we create a legacy user so we have two users with the same lowercase version of username/email
    legacy_user = factories.UserFactory(
            username="username",
            full_name="fname",
            email="user@email.com")
    legacy_user.set_password("password")


    login_form = {"type": "normal",
                  "username": "Username",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 200

    login_form = {"type": "normal",
                  "username": "User@email.com",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 200

    # 2.- If we capitalize a new version it doesn't work with username
    login_form = {"type": "normal",
                  "username": "uSername",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 401

    # neither with the email
    login_form = {"type": "normal",
                  "username": "uSer@email.com",
                  "password": "password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 401


def test_login_fail_throttling(client, settings, monkeypatch, isolated_auth_throttle_cache):
    settings.PUBLIC_REGISTER_ENABLED = True
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")

    register_form = {"username": "valid_username_login_fail",
                     "password": "valid_password",
                     "full_name": "fullname",
                     "email": "valid_username_login_fail@email.com",
                     "accepted_terms": True,
                     "type": "public"}
    response = client.post(reverse("auth-register"), register_form)

    login_form = {"type": "normal",
                  "username": "valid_username_login_fail",
                  "password": "valid_password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 200, response.data

    login_form = {"type": "normal",
                  "username": "invalid_username_login_fail",
                  "password": "invalid_password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 401, response.data

    login_form = {"type": "normal",
                  "username": "invalid_username_login_fail",
                  "password": "invalid_password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 429, response.data

    login_form = {"type": "normal",
                  "username": "valid_username_login_fail",
                  "password": "valid_password"}

    response = client.post(reverse("auth-list"), login_form)
    assert response.status_code == 429, response.data


def test_login_fail_throttling_uses_a_fresh_quota_after_whitelist_removal(client, settings, monkeypatch, isolated_auth_throttle_cache):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", ["127.0.0.1"])
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    assert client.post(reverse("auth-list"), login_form).status_code == 401
    assert client.post(reverse("auth-list"), login_form).status_code == 401

    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", [])
    assert client.post(reverse("auth-list"), login_form).status_code == 401
    assert client.post(reverse("auth-list"), login_form).status_code == 429


def test_login_fail_throttling_keeps_independent_peer_quotas(client, settings, monkeypatch, isolated_auth_throttle_cache):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.10").status_code == 401
    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.10").status_code == 429
    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.11").status_code == 401
    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.11").status_code == 429


def test_login_throttling_keeps_independent_forwarded_client_quotas(client, settings, monkeypatch, isolated_auth_throttle_cache):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setattr(settings, "AUTH_THROTTLE_TRUSTED_PROXIES", ["10.0.0.2"])
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    for client_ip in ("192.0.2.20", "192.0.2.21"):
        request_meta = {"REMOTE_ADDR": "10.0.0.2", "HTTP_X_FORWARDED_FOR": client_ip}
        assert client.post(reverse("auth-list"), login_form, **request_meta).status_code == 401
        assert client.post(reverse("auth-list"), login_form, **request_meta).status_code == 429


def test_login_fail_throttling_counts_bad_request_responses(client, settings, monkeypatch, isolated_auth_throttle_cache):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    url = reverse("auth-list")

    assert client.post(url, {}, REMOTE_ADDR="192.0.2.12").status_code == 400
    assert client.post(url, {"type": "normal", "username": "invalid", "password": "invalid"}, REMOTE_ADDR="192.0.2.12").status_code == 429


def test_login_throttling_ignores_forwarded_header_from_direct_client(client, settings, monkeypatch, isolated_auth_throttle_cache):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", ["203.0.113.7", "203.0.113.8"])
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.13", HTTP_X_FORWARDED_FOR="203.0.113.7").status_code == 401
    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR="192.0.2.13", HTTP_X_FORWARDED_FOR="203.0.113.8").status_code == 429


@pytest.mark.parametrize("remote_addr", ["", "not-an-ip"])
def test_login_throttling_does_not_whitelist_missing_or_invalid_peer(client, settings, monkeypatch, isolated_auth_throttle_cache, remote_addr):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", ["127.0.0.1"])
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR=remote_addr).status_code == 401
    assert client.post(reverse("auth-list"), login_form, REMOTE_ADDR=remote_addr).status_code == 429


@pytest.mark.parametrize(
    ("forwarded_ip", "whitelist"),
    [
        ("192.168.1.23", "192.168.1.0/24"),
        ("2001:db8::23", "2001:db8::/32"),
        ("::ffff:192.168.1.23", "192.168.1.0/24"),
    ],
)
def test_login_throttling_uses_single_forwarded_ip_from_trusted_proxy(client, settings, monkeypatch, isolated_auth_throttle_cache, forwarded_ip, whitelist):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", [whitelist])
    monkeypatch.setattr(settings, "AUTH_THROTTLE_TRUSTED_PROXIES", ["10.0.0.2"], raising=False)
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}

    for _ in range(2):
        response = client.post(reverse("auth-list"), login_form, REMOTE_ADDR="10.0.0.2", HTTP_X_FORWARDED_FOR=forwarded_ip)
        assert response.status_code == 401


@pytest.mark.parametrize("forwarded_ip", [None, "invalid", "192.0.2.1, 192.0.2.2"])
def test_login_throttling_uses_proxy_quota_for_unusable_forwarded_ip(client, settings, monkeypatch, isolated_auth_throttle_cache, forwarded_ip):
    monkeypatch.setitem(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "login-fail", "1/minute")
    monkeypatch.setitem(settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_WHITELIST", ["10.0.0.2"])
    monkeypatch.setattr(settings, "AUTH_THROTTLE_TRUSTED_PROXIES", ["10.0.0.2"], raising=False)
    login_form = {"type": "normal", "username": "invalid", "password": "invalid"}
    request_meta = {"REMOTE_ADDR": "10.0.0.2"}
    if forwarded_ip is not None:
        request_meta["HTTP_X_FORWARDED_FOR"] = forwarded_ip

    assert client.post(reverse("auth-list"), login_form, **request_meta).status_code == 401
    assert client.post(reverse("auth-list"), login_form, **request_meta).status_code == 429
