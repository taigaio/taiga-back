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

from django.core.urlresolvers import reverse

from taiga.base.utils import json

from tests import factories as f
from tests.utils import disconnect_signals, reconnect_signals

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


def test_auth_create(client):
    url = reverse('auth-list')

    user = f.UserFactory.create()

    login_data = json.dumps({
        "type": "normal",
        "username": user.username,
        "password": user.username,
    })

    result = client.post(url, login_data, content_type="application/json")
    assert result.status_code == 200


def test_auth_action_register(client, settings):
    settings.PUBLIC_REGISTER_ENABLED = True
    url = reverse('auth-register')

    register_data = json.dumps({
        "type": "public",
        "username": "test",
        "password": "test",
        "full_name": "test",
        "email": "test@test.com",
    })

    result = client.post(url, register_data, content_type="application/json")
    assert result.status_code == 201
