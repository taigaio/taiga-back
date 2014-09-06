from unittest import mock

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.userstories import services, models

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_userstories_from_bulk():
    data = """
User Story #1
User Story #2
"""
    userstories = services.get_userstories_from_bulk(data)

    assert len(userstories) == 2
    assert userstories[0].subject == "User Story #1"
    assert userstories[1].subject == "User Story #2"


@mock.patch("taiga.projects.userstories.services.db")
def test_create_userstories_in_bulk(db):
    data = """
User Story #1
User Story #2
"""
    userstories = services.create_userstories_in_bulk(data)

    db.save_in_bulk.assert_called_once_with(userstories, None, None)


@mock.patch("taiga.projects.userstories.services.db")
def test_update_userstories_order_in_bulk(db):
    data = [{"us_id": 1, "order": 1}, {"us_id": 2, "order": 2}]
    services.update_userstories_order_in_bulk(data)

    db.update_in_bulk_with_ids.assert_called_once_with([1, 2], [{"order": 1}, {"order": 2}],
                                                       model=models.UserStory)


def test_api_delete_userstory(client):
    us = f.create_userstory()
    url = reverse("userstories-detail", kwargs={"pk": us.pk})

    client.login(us.owner)
    response = client.delete(url)

    assert response.status_code == 204


def test_api_filter_by_subject(client):
    f.create_userstory()
    us = f.create_userstory(subject="some random subject")
    url = reverse("userstories-list") + "?subject=some subject"

    client.login(us.owner)
    response = client.get(url)
    number_of_stories = len(response.data)

    assert response.status_code == 200
    assert number_of_stories == 1, number_of_stories


def test_api_create_in_bulk_with_status(client):
    project = f.create_project()
    url = reverse("userstories-bulk-create")
    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "status_id": project.default_us_status.id
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data
    assert response.data[0]["status"] == project.default_us_status.id


def test_api_update_order_in_bulk(client):
    project = f.create_project()
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    url = reverse("userstories-bulk-update-order")
    data = {
        "project_id": project.id,
        "bulk_stories": [{"us_id": us1.id, "order": 1},
                         {"us_id": us2.id, "order": 2}]
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
