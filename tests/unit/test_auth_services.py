# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

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
