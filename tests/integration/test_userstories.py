from unittest import mock

import pytest

from taiga.projects.userstories import services, models

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

    db.save_in_bulk.assert_called_once_with(userstories, None)


@mock.patch("taiga.projects.userstories.services.db")
def test_update_userstories_order_in_bulk(db):
    data = [(1, 1), (2, 2)]
    services.update_userstories_order_in_bulk(data)

    db.update_in_bulk_with_ids.assert_called_once_with([1, 2], [{"order": 1}, {"order": 2}],
                                                       model=models.UserStory)
