from unittest import mock

import pytest

from django.core.urlresolvers import reverse

from taiga.projects.tasks import services

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_get_tasks_from_bulk():
    data = """
Task #1
Task #2
"""
    tasks = services.get_tasks_from_bulk(data)

    assert len(tasks) == 2
    assert tasks[0].subject == "Task #1"
    assert tasks[1].subject == "Task #2"


@mock.patch("taiga.projects.tasks.services.db")
def test_create_tasks_in_bulk(db):
    data = """
Task #1
Task #2
"""
    tasks = services.create_tasks_in_bulk(data)

    db.save_in_bulk.assert_called_once_with(tasks, None)


def test_api_update_task_tags(client):
    task = f.create_task()
    url = reverse("tasks-detail", kwargs={"pk": task.pk})
    data = {"tags": ["back", "front"], "version": task.version}

    client.login(task.owner)
    response = client.json.patch(url, data)

    assert response.status_code == 200, response.data
