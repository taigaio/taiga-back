# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid
import csv
import pytz

from datetime import datetime, timedelta
from urllib.parse import quote

from unittest import mock
from django.urls import reverse

from taiga.base.utils import json
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.userstories import services, models


from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db(transaction=True)


##############################
## Move to no swimlane
##############################

def test_api_update_orders_in_bulk_succeeds_moved_to_no_swimlane_and_to_the_begining(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #      |  us1  |         |   MOVE: us2, us3   |       |  us2  |
    #      |  us2  |         |   TO: no-swimlane  |       |  us3  |
    # -----|-------|-------  |   UNDER: st1       |       |  us1  |
    #      |       |  us3    |   AFTER: bigining  |  -----|-------|-------
    #  SW1 |       |         |                    |       |       |
    #      |       |         |                    |   SW1 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=None)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=None)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane1)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status1.id,
        "after_userstory_id": None,
        "bulk_userstories": [us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us2.id,
        us3.id,
        us1.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us2.kanban_order == 1
    assert us2.swimlane_id == None
    assert us2.status_id == status1.id
    assert us3.kanban_order == 2
    assert us3.swimlane_id == None
    assert us3.status_id == status1.id
    assert us1.kanban_order == 3
    assert us1.swimlane_id == None
    assert us1.status_id == status1.id


def test_api_update_orders_in_bulk_succeeds_moved_to_no_swimlane_and_to_the_middle(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #      |  us1  |         |   MOVE: us1, us3   |       |  us4  |
    #      |  us4  |         |   TO: no-swimlane  |       |  us1  |
    #      |  us5  |         |   UNDER: st1       |       |  us3  |
    # -----|-------|---------|   AFTER: us4       |       |  us5  |
    #  SW1 |       |  us2    |                    |  -----|-------|-------
    #      |       |  us3    |                    |   SW1 |       |  us2

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=None)
    us2 = f.create_userstory(project=project, status=status2, kanban_order=2, swimlane=swimlane1)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=3, swimlane=swimlane1)
    us4 = f.create_userstory(project=project, status=status1, kanban_order=4, swimlane=None)
    us5 = f.create_userstory(project=project, status=status1, kanban_order=4, swimlane=None)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us1.id,
        us3.id,
        us5.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    us4.refresh_from_db()
    us5.refresh_from_db()
    assert us2.kanban_order == 2
    assert us2.swimlane_id == swimlane1.id
    assert us2.status_id == status2.id
    assert us4.kanban_order == 4
    assert us4.swimlane_id == None
    assert us4.status_id == status1.id
    assert us1.kanban_order == 5
    assert us1.swimlane_id == None
    assert us1.status_id == status1.id
    assert us3.kanban_order == 6
    assert us3.swimlane_id == None
    assert us3.status_id == status1.id
    assert us5.kanban_order == 7
    assert us5.swimlane_id == None
    assert us5.status_id == status1.id


def test_api_update_orders_in_bulk_succeeds_moved_to_no_swimlane_and_to_the_end(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #      |  us1  |         |   MOVE: us3        |       |  us1  |
    #      |  us2  |         |   TO: no-swimlane  |       |  us2  |
    # -----|-------|-------  |   UNDER: st1       |       |  us3  |
    #      |       |  us3    |   AFTER: us2       |  -----|-------|-------
    #  SW1 |       |         |                    |       |       |
    #      |       |         |                    |   SW1 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=None)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=None)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane1)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status1.id,
        "after_userstory_id": us2.id,
        "bulk_userstories": [us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us3.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us1.kanban_order == 1
    assert us1.swimlane_id == None
    assert us1.status_id == status1.id
    assert us2.kanban_order == 2
    assert us2.swimlane_id == None
    assert us2.status_id == status1.id
    assert us3.kanban_order == 3
    assert us3.swimlane_id == None
    assert us3.status_id == status1.id

def test_api_update_orders_in_bulk_succeeds_moved_to_no_swimlane_and_before_a_us(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #      |  us1  |         |   MOVE: us3        |       |  us1  |
    #      |  us2  |         |   TO: no-swimlane  |       |  us3  |
    # -----|-------|-------  |   UNDER: st1       |       |  us2  |
    #      |       |  us3    |   BEFORE: us2      |  -----|-------|-------
    #  SW1 |       |         |                    |       |       |
    #      |       |         |                    |   SW1 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=None)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=None)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane1)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status1.id,
        "before_userstory_id": us2.id,
        "bulk_userstories": [us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us2.id,
        us3.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us1.kanban_order == 1
    assert us1.swimlane_id == None
    assert us1.status_id == status1.id
    assert us3.kanban_order == 2
    assert us3.swimlane_id == None
    assert us3.status_id == status1.id
    assert us2.kanban_order == 3
    assert us2.swimlane_id == None
    assert us2.status_id == status1.id

##############################
## Move to swimlane
##############################


def test_api_update_orders_in_bulk_succeeds_moved_to_a_swimlane_and_to_the_begining(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #  SW1 |  us1  |         |   MOVE: us2, us3   |       |  us2  |
    #      |  us2  |         |   TO: sw1          |   SW1 |  us3  |
    # -----|-------|-------  |   UNDER: st1       |       |  us1  |
    #      |       |  us3    |   AFTER: bigining  |  -----|-------|-------
    #  SW2 |       |         |                    |       |       |
    #      |       |         |                    |   SW2 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=swimlane1)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "swimlane_id": swimlane1.id,
        "status_id": status1.id,
        "bulk_userstories": [us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us2.id,
        us3.id,
        us1.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us2.kanban_order == 1
    assert us2.swimlane_id == swimlane1.id
    assert us2.status_id == status1.id
    assert us3.kanban_order == 2
    assert us3.swimlane_id == swimlane1.id
    assert us3.status_id == status1.id
    assert us1.kanban_order == 3
    assert us1.swimlane_id == swimlane1.id
    assert us1.status_id == status1.id


def test_api_update_orders_in_bulk_succeeds_moved_to_a_swimlane_and_to_the_middle(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #      |  us1  |         |   MOVE: us1, us3   |       |  us4  |
    #  sw1 |  us4  |         |   TO: sw1          |   SW1 |  us1  |
    #      |  us5  |         |   UNDER: st1       |       |  us3  |
    # -----|-------|---------|   AFTER: us4       |       |  us5  |
    #  SW2 |       |  us2    |                    |  -----|-------|-------
    #      |       |  us3    |                    |   SW1 |       |  us2

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, status=status2, kanban_order=2, swimlane=swimlane2)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=3, swimlane=swimlane2)
    us4 = f.create_userstory(project=project, status=status1, kanban_order=4, swimlane=swimlane1)
    us5 = f.create_userstory(project=project, status=status1, kanban_order=4, swimlane=swimlane1)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "swimlane_id": swimlane1.id,
        "status_id": status1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us1.id,
        us3.id,
        us5.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    us4.refresh_from_db()
    us5.refresh_from_db()
    assert us2.kanban_order == 2
    assert us2.swimlane_id == swimlane2.id
    assert us2.status_id == status2.id
    assert us4.kanban_order == 4
    assert us4.swimlane_id == swimlane1.id
    assert us4.status_id == status1.id
    assert us1.kanban_order == 5
    assert us1.swimlane_id == swimlane1.id
    assert us1.status_id == status1.id
    assert us3.kanban_order == 6
    assert us3.swimlane_id == swimlane1.id
    assert us3.status_id == status1.id
    assert us5.kanban_order == 7
    assert us5.swimlane_id == swimlane1.id
    assert us5.status_id == status1.id


def test_api_update_orders_in_bulk_succeeds_moved_to_a_swimlane_and_to_the_end(client):
    #
    #      |  ST1  |  ST2    |               |       |  ST1  |  ST2
    # -----|-------|-------  |               |  -----|-------|-------
    #  SW1 |  us1  |         |   MOVE: us3   |       |  us1  |
    #      |  us2  |         |   TO: sw1     |   SW1 |  us2  |
    # -----|-------|-------  |   UNDER: st1  |       |  us3  |
    #      |       |  us3    |   AFTER: us2  |  -----|-------|-------
    #  SW2 |       |         |               |       |       |
    #      |       |         |               |   SW2 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=swimlane1)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "swimlane_id": swimlane1.id,
        "status_id": status1.id,
        "after_userstory_id": us2.id,
        "bulk_userstories": [us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us3.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us1.kanban_order == 1
    assert us1.swimlane_id == swimlane1.id
    assert us1.status_id == status1.id
    assert us2.kanban_order == 2
    assert us2.swimlane_id == swimlane1.id
    assert us2.status_id == status1.id
    assert us3.kanban_order == 3
    assert us3.swimlane_id == swimlane1.id
    assert us3.status_id == status1.id

def test_api_update_orders_in_bulk_succeeds_moved_to_a_swimlane_and_before_a_us(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1  |  ST2
    # -----|-------|-------  |                    |  -----|-------|-------
    #  SW1 |  us1  |         |   MOVE: us3        |       |  us1  |
    #      |  us2  |         |   TO: sw1          |   SW1 |  us3  |
    # -----|-------|-------  |   UNDER: st1       |       |  us2  |
    #      |       |  us3    |   BEFORE: us2      |  -----|-------|-------
    #  SW2 |       |         |                    |       |       |
    #      |       |         |                    |   SW2 |       |

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swimlane1 = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project, status=status1, kanban_order=1, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, status=status1, kanban_order=2, swimlane=swimlane1)
    us3 = f.create_userstory(project=project, status=status2, kanban_order=1, swimlane=swimlane2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "swimlane_id": swimlane1.id,
        "status_id": status1.id,
        "before_userstory_id": us2.id,
        "bulk_userstories": [us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us3.id,
        us2.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)

    us1.refresh_from_db()
    us2.refresh_from_db()
    us3.refresh_from_db()
    assert us1.kanban_order == 1
    assert us1.swimlane_id == swimlane1.id
    assert us1.status_id == status1.id
    assert us3.kanban_order == 2
    assert us3.swimlane_id == swimlane1.id
    assert us3.status_id == status1.id
    assert us2.kanban_order == 3
    assert us2.swimlane_id == swimlane1.id
    assert us2.status_id == status1.id


##############################
## Data errors
##############################

def test_api_update_orders_in_bulk_invalid_userstories(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory()

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "bulk_userstories" in response.data


def test_api_update_orders_in_bulk_invalid_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create()
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "status_id" in response.data


def test_api_update_orders_in_bulk_invalid_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create()
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "swimlane_id" in response.data


def test_api_update_orders_in_bulk_invalid_after_us_because_project(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory()

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "after_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_after_us_because_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, swimlane=swl1, status=status2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "after_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_after_us_because_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    swl2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, status=status, swimlane=swl2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "after_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_after_us_because_no_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, status=status, swimlane=None)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "after_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_before_us_because_project(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory()

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "before_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "before_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_before_us_because_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, swimlane=swl1, status=status2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "before_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "before_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_before_us_because_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    swl2 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, status=status, swimlane=swl2)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "before_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "before_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_before_us_because_no_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, status=status, swimlane=None)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "before_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "before_userstory_id" in response.data


def test_api_update_orders_in_bulk_invalid_before_us_because_after_us_exist(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.UserStoryStatusFactory.create(project=project)
    swl1 = f.SwimlaneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)
    us4 = f.create_userstory(project=project, swimlane=swl1, status=status)

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "swimlane_id": swl1.id,
        "before_userstory_id": us4.id,
        "after_userstory_id": us4.id,
        "bulk_userstories": [us1.id,
                             us2.id,
                             us3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "before_userstory_id" in response.data



##############################
## Move after user story status is deleted
##############################

def test_api_delete_userstory_status(client):
    #
    #      |  ST1  |  ST2    |                    |       |  ST1
    # -----|-------|-------  |                    |  -----|-------
    #  SW1 | us111 | us121   |   DELETE: st2      |       | us111
    #      | us112 | us122   |   AND MOVE TO: st1 |   SW1 | us112
    # -----|-------|-------  |                    |       | us121
    #      | us211 |  us221  |                    |       | us122
    #  SW2 |       |         |                    |  -----|-------
    #      |       |         |                    |   SW2 | us211
    #      |       |         |                    |       | us222

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    st1 = f.UserStoryStatusFactory.create(project=project, order=1)
    st2 = f.UserStoryStatusFactory.create(project=project, order=2)
    swl1 = f.SwimlaneFactory.create(project=project, order=1)
    swl2 = f.SwimlaneFactory.create(project=project, order=2)
    us111 = f.create_userstory(project=project, swimlane=swl1, status=st1, kanban_order=20)
    us112 = f.create_userstory(project=project, swimlane=swl1, status=st1, kanban_order=40)
    us121 = f.create_userstory(project=project, swimlane=swl1, status=st2, kanban_order=35)
    us122 = f.create_userstory(project=project, swimlane=swl1, status=st2, kanban_order=45)
    us211 = f.create_userstory(project=project, swimlane=swl2, status=st1, kanban_order=2)
    us221 = f.create_userstory(project=project, swimlane=swl2, status=st2, kanban_order=1)

    uss_qs = (models.UserStory.objects.values_list("id", flat=True)
                                      .order_by("status__order", "swimlane__order", "kanban_order"))
    url = reverse("userstory-statuses-detail", kwargs={"pk": st2.pk}) + f"?moveTo={st1.id}"
    assert list(uss_qs) == [us111.id, us112.id, us211.id, us121.id, us122.id, us221.id]

    client.login(project.owner)
    response = client.json.delete(url)
    assert response.status_code == 204, response.data

    uss_qs = (models.UserStory.objects.values_list("id", flat=True)
                                      .order_by("status__order", "swimlane__order", "kanban_order"))
    assert list(uss_qs) == [us111.id, us112.id, us121.id, us122.id, us211.id, us221.id]


##############################
## Close and Open USs after they are moved, history entries and webhooks should be created too
##############################

@mock.patch('taiga.webhooks.tasks._send_request')
def test_userstories_are_closed_after_moving_in_bulk_to_a_closed_status(send_request_mock, client, settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status_opened = f.UserStoryStatusFactory.create(project=project, order=1, is_closed=False)
    status_closed = f.UserStoryStatusFactory.create(project=project, order=2, is_closed=True)
    us1 = f.create_userstory(project=project, status=status_closed, is_closed=True, kanban_order=3)
    us2 = f.create_userstory(project=project, status=status_opened, is_closed=False, kanban_order=2)

    assert HistoryEntry.objects.all().count() == 0
    assert send_request_mock.call_count == 0

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status_closed.id,
        "after_userstory_id": None,
        "bulk_userstories": [us1.id,
                             us2.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us1.id,
        us2.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)


    assert us1.is_closed and us1.status == status_closed
    assert not us2.is_closed and us2.status == status_opened
    us1.refresh_from_db()
    us2.refresh_from_db()
    assert us1.is_closed and us1.status == status_closed
    assert us2.is_closed and us2.status == status_closed
    assert HistoryEntry.objects.all().count() == 2
    assert send_request_mock.call_count == 2


@mock.patch('taiga.webhooks.tasks._send_request')
def test_userstories_are_opened_after_moving_in_bulk_to_a_opened_status(send_request_mock, client, settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status_opened = f.UserStoryStatusFactory.create(project=project, order=1, is_closed=False)
    status_closed = f.UserStoryStatusFactory.create(project=project, order=2, is_closed=True)
    us1 = f.create_userstory(project=project, status=status_closed, is_closed=True, kanban_order=3)
    us2 = f.create_userstory(project=project, status=status_opened, is_closed=False, kanban_order=2)

    assert HistoryEntry.objects.all().count() == 0
    assert send_request_mock.call_count == 0

    url = reverse("userstories-bulk-update-kanban-order")

    data = {
        "project_id": project.id,
        "status_id": status_opened.id,
        "after_userstory_id": None,
        "bulk_userstories": [us1.id,
                             us2.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        us1.id,
        us2.id,
    ]
    res = (project.user_stories.filter(id__in=updated_ids)
                               .values("id", "swimlane", "kanban_order", "status")
                               .order_by("kanban_order", "id"))
    assert response.json() == list(res)


    assert us1.is_closed and us1.status == status_closed
    assert not us2.is_closed and us2.status == status_opened
    us1.refresh_from_db()
    us2.refresh_from_db()
    assert not us1.is_closed and us1.status == status_opened
    assert not us2.is_closed and us2.status == status_opened
    assert HistoryEntry.objects.all().count() == 2
    assert send_request_mock.call_count == 2
