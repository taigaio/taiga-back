# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from tests import factories as f
from tests.utils import helper_test_http_method

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.user = f.UserFactory.create()
    return m


def test_feedback_create(client, data):
    url = reverse("feedback-list")
    users = [None, data.user]

    feedback_data = {"comment": "One feedback comment"}
    feedback_data = json.dumps(feedback_data)

    results = helper_test_http_method(client, 'post', url, feedback_data, users)
    assert results == [401, 200]
