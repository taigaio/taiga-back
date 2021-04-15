# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

import pytest

from .. import factories as f

from taiga.base import exceptions as exc
from taiga.auth.tokens import get_token_for_user, get_user_for_token


pytestmark = pytest.mark.django_db(transaction=True)


def test_valid_token():
    user = f.UserFactory.create(email="old@email.com")
    token = get_token_for_user(user, "testing_scope")
    user_from_token = get_user_for_token(token, "testing_scope")
    assert user.id == user_from_token.id


@pytest.mark.xfail(raises=exc.NotAuthenticated)
def test_invalid_token():
    f.UserFactory.create(email="old@email.com")
    get_user_for_token("testing_invalid_token", "testing_scope")


@pytest.mark.xfail(raises=exc.NotAuthenticated)
def test_invalid_token_expiration():
    user = f.UserFactory.create(email="old@email.com")
    token = get_token_for_user(user, "testing_scope")
    get_user_for_token(token, "testing_scope", max_age=1)


@pytest.mark.xfail(raises=exc.NotAuthenticated)
def test_invalid_token_scope():
    user = f.UserFactory.create(email="old@email.com")
    token = get_token_for_user(user, "testing_scope")
    get_user_for_token(token, "testing_invalid_scope")
