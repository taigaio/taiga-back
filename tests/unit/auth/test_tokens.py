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

from datetime import datetime, timedelta
from unittest.mock import patch

from jose import jwt

from taiga.base import exceptions as exc
from taiga.auth.exceptions import TokenError
from taiga.auth.settings import api_settings
from taiga.auth.state import token_backend
from taiga.auth.tokens import (
    AccessToken, CancelToken, RefreshToken, Token, UntypedToken,
)
from taiga.auth.utils import (
    aware_utcnow, datetime_to_epoch, make_utc,
)

from tests import factories as f

from .utils import override_api_settings


##########################################################
## Token
##########################################################

class MyToken(Token):
    token_type = 'test'
    lifetime = timedelta(days=1)


@pytest.fixture
def token():
    return MyToken()


def test_init_no_token_type_or_lifetime():
    class MyTestToken(Token):
        pass

    with pytest.raises(TokenError):
        MyTestToken()

    MyTestToken.token_type = 'test'

    with pytest.raises(TokenError):
        MyTestToken()

    del MyTestToken.token_type
    MyTestToken.lifetime = timedelta(days=1)

    with pytest.raises(TokenError):
        MyTestToken()

    MyTestToken.token_type = 'test'
    MyTestToken()


def test_init_no_token_given():
    now = make_utc(datetime(year=2000, month=1, day=1))

    with patch('taiga.auth.tokens.aware_utcnow') as fake_aware_utcnow:
        fake_aware_utcnow.return_value = now
        t = MyToken()

    assert t.current_time == now
    assert t.token is None

    assert len(t.payload) == 3
    assert t.payload['exp'] == datetime_to_epoch(now + MyToken.lifetime)
    assert 'jti' in t.payload
    assert t.payload[api_settings.TOKEN_TYPE_CLAIM] == MyToken.token_type


def test_init_token_given():
    # Test successful instantiation
    original_now = aware_utcnow()

    with patch('taiga.auth.tokens.aware_utcnow') as fake_aware_utcnow:
        fake_aware_utcnow.return_value = original_now
        good_token = MyToken()

    good_token['some_value'] = 'arst'
    encoded_good_token = str(good_token)

    now = aware_utcnow()

    # Create new token from encoded token
    with patch('taiga.auth.tokens.aware_utcnow') as fake_aware_utcnow:
        fake_aware_utcnow.return_value = now
        # Should raise no exception
        t = MyToken(encoded_good_token)

    # Should have expected properties
    assert t.current_time == now
    assert t.token == encoded_good_token

    assert len(t.payload) == 4
    assert t['some_value'] == 'arst'
    assert t['exp'] == datetime_to_epoch(original_now + MyToken.lifetime)
    assert t[api_settings.TOKEN_TYPE_CLAIM] == MyToken.token_type
    assert 'jti' in t.payload


def test_init_bad_sig_token_given():
    # Test backend rejects encoded token (expired or bad signature)
    payload = {'foo': 'bar'}
    payload['exp'] = aware_utcnow() + timedelta(days=1)
    token_1 = jwt.encode(payload, api_settings.SIGNING_KEY, algorithm='HS256')
    payload['foo'] = 'baz'
    token_2 = jwt.encode(payload, api_settings.SIGNING_KEY, algorithm='HS256')

    token_2_payload = token_2.rsplit('.', 1)[0]
    token_1_sig = token_1.rsplit('.', 1)[-1]
    invalid_token = token_2_payload + '.' + token_1_sig

    with pytest.raises(TokenError):
        MyToken(invalid_token)


def test_init_bad_sig_token_given_no_verify():
    # Test backend rejects encoded token (expired or bad signature)
    payload = {'foo': 'bar'}
    payload['exp'] = aware_utcnow() + timedelta(days=1)
    token_1 = jwt.encode(payload, api_settings.SIGNING_KEY, algorithm='HS256')
    payload['foo'] = 'baz'
    token_2 = jwt.encode(payload, api_settings.SIGNING_KEY, algorithm='HS256')

    token_2_payload = token_2.rsplit('.', 1)[0]
    token_1_sig = token_1.rsplit('.', 1)[-1]
    invalid_token = token_2_payload + '.' + token_1_sig

    t = MyToken(invalid_token, verify=False)

    assert t.payload == payload


def test_init_expired_token_given():
    t = MyToken()
    t.set_exp(lifetime=-timedelta(seconds=1))

    with pytest.raises(TokenError):
        MyToken(str(t))


def test_init_no_type_token_given():
    t = MyToken()
    del t[api_settings.TOKEN_TYPE_CLAIM]

    with pytest.raises(TokenError):
        MyToken(str(t))


def test_init_wrong_type_token_given():
    t = MyToken()
    t[api_settings.TOKEN_TYPE_CLAIM] = 'wrong_type'

    with pytest.raises(TokenError):
        MyToken(str(t))


def test_init_no_jti_token_given():
    t = MyToken()
    del t['jti']

    with pytest.raises(TokenError):
        MyToken(str(t))


def test_str():
    token = MyToken()
    token.set_exp(
        from_time=make_utc(datetime(year=2000, month=1, day=1)),
        lifetime=timedelta(seconds=0),
    )

    # Delete all but one claim.  We want our lives to be easy and for there
    # to only be a couple of possible encodings.  We're only testing that a
    # payload is successfully encoded here, not that it has specific
    # content.
    del token[api_settings.TOKEN_TYPE_CLAIM]
    del token['jti']

    # Should encode the given token
    encoded_token = str(token)

    # Token could be one of two depending on header dict ordering
    assert encoded_token in (
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjk0NjY4NDgwMH0.VKoOnMgmETawjDZwxrQaHG0xHdo6xBodFy6FXJzTVxs',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjk0NjY4NDgwMH0.iqxxOHV63sjeqNR1GDxX3LPvMymfVB76sOIDqTbjAgk',
    )


def test_repr(token):
    assert repr(token) == repr(token.payload)


def test_getitem(token):
    assert token['exp'], token.payload['exp']


def test_setitem(token):
    token['test'] = 1234
    assert token.payload['test'], 1234


def test_delitem(token):
    token['test'] = 1234
    assert token.payload['test'], 1234

    del token['test']
    assert 'test' not in token


def test_contains(token):
    assert 'exp' in token


def test_get(token):
    token['test'] = 1234

    assert 1234 == token.get('test')
    assert 1234 == token.get('test', 2345)

    assert token.get('does_not_exist') is None
    assert 1234 == token.get('does_not_exist', 1234)


def test_set_jti():
    token = MyToken()
    old_jti = token['jti']

    token.set_jti()

    assert 'jti' in token
    assert old_jti != token['jti']


def test_set_exp():
    now = make_utc(datetime(year=2000, month=1, day=1))

    token = MyToken()
    token.current_time = now

    # By default, should add 'exp' claim to token using `self.current_time`
    # and the TOKEN_LIFETIME setting
    token.set_exp()
    assert token['exp'] == datetime_to_epoch(now + MyToken.lifetime)

    # Should allow overriding of beginning time, lifetime, and claim name
    token.set_exp(claim='refresh_exp', from_time=now, lifetime=timedelta(days=1))

    assert 'refresh_exp' in token
    assert token['refresh_exp'] == datetime_to_epoch(now + timedelta(days=1))


def test_check_exp():
    token = MyToken()

    # Should raise an exception if no claim of given kind
    with pytest.raises(TokenError):
        token.check_exp('non_existent_claim')

    current_time = token.current_time
    lifetime = timedelta(days=1)
    exp = token.current_time + lifetime

    token.set_exp(lifetime=lifetime)

    # By default, checks 'exp' claim against `self.current_time`.  Should
    # raise an exception if claim has expired.
    token.current_time = exp
    with pytest.raises(TokenError):
        token.check_exp()

    token.current_time = exp + timedelta(seconds=1)
    with pytest.raises(TokenError):
        token.check_exp()

    # Otherwise, should raise no exception
    token.current_time = current_time
    token.check_exp()

    # Should allow specification of claim to be examined and timestamp to
    # compare against

    # Default claim
    with pytest.raises(TokenError):
        token.check_exp(current_time=exp)

    token.set_exp('refresh_exp', lifetime=timedelta(days=1))

    # Default timestamp
    token.check_exp('refresh_exp')

    # Given claim and timestamp
    with pytest.raises(TokenError):
        token.check_exp('refresh_exp', current_time=current_time + timedelta(days=1))
    with pytest.raises(TokenError):
        token.check_exp('refresh_exp', current_time=current_time + timedelta(days=2))


@pytest.mark.django_db
def test_for_user():
    username = 'test_user'
    user = f.UserFactory(username=username)

    token = MyToken.for_user(user)

    user_id = getattr(user, api_settings.USER_ID_FIELD)
    if not isinstance(user_id, int):
        user_id = str(user_id)

    assert token[api_settings.USER_ID_CLAIM] == user_id

    # Test with non-int user id
    with override_api_settings(USER_ID_FIELD='username'):
        token = MyToken.for_user(user)

    assert token[api_settings.USER_ID_CLAIM] == username


def test_get_token_backend():
    token = MyToken()

    assert token.get_token_backend() == token_backend


##########################################################
## AccessToken
##########################################################

def test_access_token_init():
    # Should set token type claim
    token = AccessToken()
    assert token[api_settings.TOKEN_TYPE_CLAIM] == 'access'


##########################################################
## RefreshToken
##########################################################

def test_refresh_token_init():
    # Should set token type claim
    token = RefreshToken()
    assert token[api_settings.TOKEN_TYPE_CLAIM] == 'refresh'


def test_refresh_token_access_token():
    # Should create an access token from a refresh token
    refresh = RefreshToken()
    refresh['test_claim'] = 'arst'

    access = refresh.access_token

    assert isinstance(access, AccessToken)
    assert access[api_settings.TOKEN_TYPE_CLAIM] == 'access'

    # Should keep all copyable claims from refresh token
    assert refresh['test_claim'] == access['test_claim']

    # Should not copy certain claims from refresh token
    for claim in RefreshToken.no_copy_claims:
        assert refresh[claim] != access[claim]


##########################################################
## CancelToken
##########################################################

def test_cancel_token_init():
    # Should set token type claim
    token = CancelToken()
    assert token[api_settings.TOKEN_TYPE_CLAIM] == 'cancel_account'


##########################################################
## UntypedToken
##########################################################

def test_untyped_token_it_should_accept_and_verify_any_type_of_token():
    access_token = AccessToken()
    refresh_token = RefreshToken()
    cancel_token = CancelToken()

    for t in (access_token, refresh_token, cancel_token):
        untyped_token = UntypedToken(str(t))

        assert t.payload == untyped_token.payload


def test_untyped_token_it_should_expire_immediately_if_made_from_scratch():
    t = UntypedToken()

    assert t[api_settings.TOKEN_TYPE_CLAIM] == 'untyped'

    with pytest.raises(TokenError):
        t.check_exp()
