# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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
from unittest.mock import patch
from taiga.auth import services
from taiga.base import exceptions as exc
from taiga.base.api.request import Request
from django.http import HttpRequest, QueryDict


@patch("taiga.auth.services.make_auth_response_data")
@patch("taiga.auth.services.get_and_validate_user")
def test_normal_login_func_transforms_input_into_str(get_and_validate_user_mock, make_auth_response_data_mock):
    http_request = HttpRequest()
    request = Request(http_request)
    request._data = QueryDict(mutable=True)
    request._data["username"] = {"username": "myusername"}
    request._data["password"] = 123

    services.normal_login_func(request)

    get_and_validate_user_mock.assert_called_once_with(
        username="{'username': 'myusername'}",
        password="123",
    )
    make_auth_response_data_mock.assert_called()
