import pytest
from unittest import mock

from django.core.urlresolvers import reverse
from django.core.cache import cache

from taiga.base.utils import json

from .. import factories as f

pytestmark = pytest.mark.django_db


anon_rate_path = "taiga.base.throttling.AnonRateThrottle.get_rate"
user_rate_path = "taiga.base.throttling.UserRateThrottle.get_rate"
import_rate_path = "taiga.export_import.throttling.ImportModeRateThrottle.get_rate"


def test_anonimous_throttling_policy(client, settings):
    project = f.create_project()
    url = reverse("projects-list")

    with mock.patch(anon_rate_path) as anon_rate, \
            mock.patch(user_rate_path) as user_rate, \
            mock.patch(import_rate_path) as import_rate:
        anon_rate.return_value = "2/day"
        user_rate.return_value = "4/day"
        import_rate.return_value = "7/day"

        cache.clear()
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 429


def test_user_throttling_policy(client, settings):
    project = f.create_project()
    membership = f.MembershipFactory.create(project=project, user=project.owner, is_owner=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    client.login(project.owner)

    with mock.patch(anon_rate_path) as anon_rate, \
            mock.patch(user_rate_path) as user_rate, \
            mock.patch(import_rate_path) as import_rate:
        anon_rate.return_value = "2/day"
        user_rate.return_value = "4/day"
        import_rate.return_value = "7/day"

        cache.clear()
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 200
        response = client.json.get(url)
        assert response.status_code == 429

    client.logout()


def test_import_mode_throttling_policy(client, settings):
    project = f.create_project()
    membership = f.MembershipFactory.create(project=project, user=project.owner, is_owner=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Test"
    }

    client.login(project.owner)

    with mock.patch(anon_rate_path) as anon_rate, \
            mock.patch(user_rate_path) as user_rate, \
            mock.patch(import_rate_path) as import_rate:
        anon_rate.return_value = "2/day"
        user_rate.return_value = "4/day"
        import_rate.return_value = "7/day"

        cache.clear()
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 429

    client.logout()
