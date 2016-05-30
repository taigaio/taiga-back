# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from .. import factories as f

from taiga.base import exceptions as exc
from taiga.auth.tokens import get_token_for_user, get_user_for_token


pytestmark = pytest.mark.django_db


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
