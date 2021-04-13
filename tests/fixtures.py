# -*- coding: utf-8 -*-
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
