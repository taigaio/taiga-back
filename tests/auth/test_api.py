# -*- coding: utf-8 -*-
import pytest
from unittest import mock

from rest_framework.reverse import reverse

from ..factories import DomainFactory

pytestmark = pytest.mark.django_db


def setup_module(module):
    module.patcher = mock.patch("taiga.domains.base.get_default_domain", DomainFactory.build)
    module.patcher.start()


def teardown_module(module):
    module.patcher.stop()


def test_respond_400_if_credentials_are_invalid(client):
    response = client.post(reverse("auth-list"), {"username": "john", "password": "smith"})
    assert response.status_code == 400
