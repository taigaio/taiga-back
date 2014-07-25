import pytest

from django.conf import settings
from django.core.urlresolvers import reverse

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_api_create_project(client):
    f.ProjectTemplateFactory.create(slug=settings.DEFAULT_PROJECT_TEMPLATE)
    user = f.UserFactory.create()
    url = reverse("projects-list")
    data = {"name": "project name", "description": "project description"}

    client.login(user)
    response = client.json.post(url, data)

    assert response.status_code == 201
