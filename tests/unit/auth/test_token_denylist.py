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
from django.core.management import call_command
from unittest.mock import patch

from taiga.auth.exceptions import TokenError
from taiga.auth.settings import api_settings
from taiga.auth.token_denylist.models import (
    DenylistedToken, OutstandingToken,
)
from taiga.auth.tokens import (
    AccessToken, RefreshToken
)
from taiga.auth.utils import aware_utcnow, datetime_from_epoch

from tests import factories as f


pytestmark = pytest.mark.django_db


def test_refresh_tokens_are_added_to_outstanding_list():
    user = f.UserFactory(
        username='test_user',
        password='test_password',
    )
    token = RefreshToken.for_user(user)

    qs = OutstandingToken.objects.all()
    outstanding_token = qs.first()

    assert qs.count() == 1
    assert outstanding_token.user == user
    assert outstanding_token.jti == token['jti']
    assert outstanding_token.token == str(token)
    assert outstanding_token.created_at == token.current_time
    assert outstanding_token.expires_at == datetime_from_epoch(token['exp'])


def test_access_tokens_are_not_added_to_outstanding_list():
    user = f.UserFactory(
        username='test_user',
        password='test_password',
    )
    AccessToken.for_user(user)

    qs = OutstandingToken.objects.all()

    assert qs.exists() == False


def test_token_will_not_validate_if_denylisted():
    user = f.UserFactory(
        username='test_user',
        password='test_password',
    )
    token = RefreshToken.for_user(user)
    outstanding_token = OutstandingToken.objects.first()

    # Should raise no exception
    RefreshToken(str(token))

    # Add token to denylist
    DenylistedToken.objects.create(token=outstanding_token)

    with pytest.raises(TokenError) as e:
        # Should raise exception
        RefreshToken(str(token))
        assert 'denylisted' in e.exception.args[0]


def test_tokens_can_be_manually_denylisted():
    user = f.UserFactory(
        username='test_user',
        password='test_password',
    )
    token = RefreshToken.for_user(user)

    # Should raise no exception
    RefreshToken(str(token))

    assert OutstandingToken.objects.count() == 1

    # Add token to denylist
    denylisted_token, created = token.denylist()

    # Should not add token to outstanding list if already present
    assert OutstandingToken.objects.count() == 1

    # Should return denylist record and boolean to indicate creation
    assert denylisted_token.token.jti == token['jti']
    assert created == True

    with pytest.raises(TokenError) as e:
        # Should raise exception
        RefreshToken(str(token))
        assert 'denylisted' in e.exception.args[0]

    # If denylisted token already exists, indicate no creation through
    # boolean
    denylisted_token, created = token.denylist()
    assert denylisted_token.token.jti == token['jti']
    assert created == False

    # Should add token to outstanding list if not already present
    new_token = RefreshToken()
    denylisted_token, created = new_token.denylist()
    assert denylisted_token.token.jti == new_token['jti']
    assert created == True

    assert OutstandingToken.objects.count() == 2


def test_flush_expired_tokens_should_delete_any_expired_tokens():
    user = f.UserFactory(
        username='test_user',
        password='test_password',
    )
    # Make some tokens that won't expire soon
    not_expired_1 = RefreshToken.for_user(user)
    not_expired_2 = RefreshToken.for_user(user)
    not_expired_3 = RefreshToken()

    # Denylist fresh tokens
    not_expired_2.denylist()
    not_expired_3.denylist()

    # Make tokens with fake exp time that will expire soon
    fake_now = aware_utcnow() - api_settings.REFRESH_TOKEN_LIFETIME

    with patch('taiga.auth.tokens.aware_utcnow') as fake_aware_utcnow:
        fake_aware_utcnow.return_value = fake_now
        expired_1 = RefreshToken.for_user(user)
        expired_2 = RefreshToken()

    # Denylist expired tokens
    expired_1.denylist()
    expired_2.denylist()

    # Make another token that won't expire soon
    not_expired_4 = RefreshToken.for_user(user)

    # Should be certain number of outstanding tokens and denylisted
    # tokens
    assert OutstandingToken.objects.count() == 6
    assert DenylistedToken.objects.count() == 4

    call_command('flushexpiredtokens')

    # Expired outstanding *and* denylisted tokens should be gone
    assert OutstandingToken.objects.count() == 4
    assert DenylistedToken.objects.count() == 2

    assert (
        [i.jti for i in OutstandingToken.objects.order_by('id')] ==
        [not_expired_1['jti'], not_expired_2['jti'], not_expired_3['jti'], not_expired_4['jti']]
    )
    assert (
        [i.token.jti for i in DenylistedToken.objects.order_by('id')] ==
        [not_expired_2['jti'], not_expired_3['jti']]
    )
