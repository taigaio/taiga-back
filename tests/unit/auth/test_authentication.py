# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC
#
# The code is partially taken (and modified) from djangorestframework-simplejwt v. 4.7.1
# (https://github.com/jazzband/djangorestframework-simplejwt/tree/5997c1aee8ad5182833d6b6759e44ff0a704edb4)
# that is licensed under the following terms:
#
#   Copyright 2017 David Sanders
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of
#   this software and associated documentation files (the "Software"), to deal in
#   the Software without restriction, including without limitation the rights to
#   use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
#   of the Software, and to permit persons to whom the Software is furnished to do
#   so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import pytest

from datetime import timedelta
from importlib import reload

from taiga.auth import authentication
from taiga.auth.exceptions import (
    AuthenticationFailed, InvalidToken,
)
from taiga.auth.models import TokenUser
from taiga.auth.settings import api_settings
from taiga.auth.tokens import AccessToken, CancelToken

from tests import factories as f

from .utils import override_api_settings, APIRequestFactory


###################################
# JWTAuthentication
###################################

factory = APIRequestFactory()

fake_token = b'TokenMcTokenface'
fake_header = b'Bearer ' + fake_token


def test_jwt_authentication_get_header(backend = authentication.JWTAuthentication()):
    # Should return None if no authorization header
    request = factory.get('/test-url/')
    assert backend.get_header(request) is None

    # Should pull correct header off request
    request = factory.get('/test-url/', HTTP_AUTHORIZATION=fake_header)
    assert backend.get_header(request) == fake_header

    # Should work for unicode headers
    request = factory.get('/test-url/', HTTP_AUTHORIZATION=fake_header.decode('utf-8'))
    assert backend.get_header(request) == fake_header

    # Should work with the x_access_token
    with override_api_settings(AUTH_HEADER_NAME='HTTP_X_ACCESS_TOKEN'):
        # Should pull correct header off request when using X_ACCESS_TOKEN
        request = factory.get('/test-url/', HTTP_X_ACCESS_TOKEN=fake_header)
        assert backend.get_header(request) == fake_header

        # Should work for unicode headers when using
        request = factory.get('/test-url/', HTTP_X_ACCESS_TOKEN=fake_header.decode('utf-8'))
        assert backend.get_header(request) == fake_header


def test_jwt_authentication_get_raw_token(backend = authentication.JWTAuthentication()):
    # Should return None if header lacks correct type keyword
    with override_api_settings(AUTH_HEADER_TYPES='JWT'):
        reload(authentication)
        assert backend.get_raw_token(fake_header) is None
    reload(authentication)

    # Should return None if an empty AUTHORIZATION header is sent
    assert backend.get_raw_token(b'') is None

    # Should raise error if header is malformed
    with pytest.raises(AuthenticationFailed):
        backend.get_raw_token(b'Bearer one two')

    with pytest.raises(AuthenticationFailed):
        backend.get_raw_token(b'Bearer')

    # Otherwise, should return unvalidated token in header
    assert backend.get_raw_token(fake_header) ==  fake_token

    # Should return token if header has one of many valid token types
    with override_api_settings(AUTH_HEADER_TYPES=('JWT', 'Bearer')):
        reload(authentication)
        assert backend.get_raw_token(fake_header) == fake_token

    reload(authentication)


def test_jwt_authentication_get_validated_token(backend = authentication.JWTAuthentication()):
    # Should raise InvalidToken if token not valid
    AuthToken = api_settings.AUTH_TOKEN_CLASSES[0]
    token = AuthToken()
    token.set_exp(lifetime=-timedelta(days=1))
    with pytest.raises(InvalidToken):
        backend.get_validated_token(str(token))

    # Otherwise, should return validated token
    token.set_exp()
    assert backend.get_validated_token(str(token)).payload == token.payload

    # Should not accept tokens not included in AUTH_TOKEN_CLASSES
    cancel_token = CancelToken()
    with override_api_settings(AUTH_TOKEN_CLASSES=(
        'taiga.auth.tokens.AccessToken',
    )):
        with pytest.raises(InvalidToken) as e:
            backend.get_validated_token(str(cancel_token))

        messages = e.value.detail['messages']
        assert len(messages) == 1
        assert {
            'token_class': 'AccessToken',
            'token_type': 'access',
            'message': 'Token has wrong type',
        } == messages[0]

    # Should accept tokens included in AUTH_TOKEN_CLASSES
    access_token = AccessToken()
    cancel_token = CancelToken()
    with override_api_settings(AUTH_TOKEN_CLASSES=(
        'taiga.auth.tokens.AccessToken',
        'taiga.auth.tokens.CancelToken',
    )):
        backend.get_validated_token(str(access_token))
        backend.get_validated_token(str(cancel_token))


@pytest.mark.django_db
def test_jwt_authentication_get_user(backend = authentication.JWTAuthentication()):
    payload = {'some_other_id': 'foo'}

    # Should raise error if no recognizable user identification
    with pytest.raises(InvalidToken):
        backend.get_user(payload)

    payload[api_settings.USER_ID_CLAIM] = 42

    # Should raise exception if user not found
    with pytest.raises(AuthenticationFailed):
        backend.get_user(payload)

    u = f.UserFactory(username='markhamill')
    u.is_active = False
    u.save()

    payload[api_settings.USER_ID_CLAIM] = getattr(u, api_settings.USER_ID_FIELD)

    # Should raise exception if user is inactive
    with pytest.raises(AuthenticationFailed):
        backend.get_user(payload)

    u.is_active = True
    u.save()

    # Otherwise, should return correct user
    assert backend.get_user(payload).id == u.id


###################################
# JWTAuthentication
###################################

def test_jwt_token_user_authentication_get_user(backend = authentication.JWTTokenUserAuthentication()):
    payload = {'some_other_id': 'foo'}

    # Should raise error if no recognizable user identification
    with pytest.raises(InvalidToken):
        backend.get_user(payload)

    payload[api_settings.USER_ID_CLAIM] = 42

    # Otherwise, should return a token user object
    user = backend.get_user(payload)

    assert isinstance(user, TokenUser)
    assert user.id == 42


def test_jwt_token_user_authentication_custom_tokenuser(backend = authentication.JWTTokenUserAuthentication()):
    from django.utils.functional import cached_property

    class BobSaget(TokenUser):
        @cached_property
        def username(self):
            return "bsaget"

    temp = api_settings.TOKEN_USER_CLASS
    api_settings.TOKEN_USER_CLASS = BobSaget

    # Should return a token user object
    payload = {api_settings.USER_ID_CLAIM: 42}
    user = backend.get_user(payload)

    assert isinstance(user, api_settings.TOKEN_USER_CLASS)
    assert user.id == 42
    assert user.username == "bsaget"

    # Restore default TokenUser for future tests
    api_settings.TOKEN_USER_CLASS = temp
