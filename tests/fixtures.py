# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
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
from unittest import mock
import functools


class Object:
    pass


@pytest.fixture
def object():
    return Object()


class PartialMethodCaller:
    def __init__(self, obj, **partial_params):
        self.obj = obj
        self.partial_params = partial_params

    def __getattr__(self, name):
        return functools.partial(getattr(self.obj, name), **self.partial_params)


@pytest.fixture
def client():
    from django.test.client import Client

    class _Client(Client):
        def login(self, user=None, backend="django.contrib.auth.backends.ModelBackend", **credentials):
            if user is None:
                return super().login(**credentials)

            with mock.patch('django.contrib.auth.authenticate') as authenticate:
                user.backend = backend
                authenticate.return_value = user
                return super().login(**credentials)

        @property
        def json(self):
            return PartialMethodCaller(obj=self, content_type='application/json;charset="utf-8"')

    return _Client()


@pytest.fixture
def outbox():
    from django.core import mail

    return mail.outbox
