# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from tests import factories as f

from taiga.base.utils import json

import pytest
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return f.UserFactory.create()


def test_create_feedback(client, user):
    url = reverse("feedback-list")

    feedback_data = {"comment": "One feedback comment"}
    feedback_data = json.dumps(feedback_data)

    client.login(user)

    response = client.post(url, feedback_data, content_type="application/json")
    assert response.status_code == 200

    assert response.data.get("id", None)
    assert response.data.get("created_date", None)
    assert response.data.get("full_name", user.full_name)
    assert response.data.get("email", user.email)

    client.logout()


def test_create_feedback_without_comments(client, user):
    url = reverse("feedback-list")

    feedback_data = json.dumps({})

    client.login(user)

    response = client.post(url, feedback_data, content_type="application/json")
    assert response.status_code == 400
    assert response.data.get("comment", None)

    client.logout()
