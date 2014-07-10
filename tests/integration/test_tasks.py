from unittest import mock

import pytest

from taiga.projects.tasks import services

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
