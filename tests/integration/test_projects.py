from django.core.urlresolvers import reverse
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_create_project(client):
    user = f.create_user()
    url = reverse("projects-list")
    data = {"name": "project name", "description": "project description"}

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_partially_update_project(client):
    project = f.create_project()
    url = reverse("projects-detail", kwargs={"pk": project.pk})
    data = {"name": ""}

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400
