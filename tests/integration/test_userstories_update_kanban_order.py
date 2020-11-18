# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import uuid
import csv
import pytz

from datetime import datetime, timedelta
from urllib.parse import quote

from unittest import mock
from django.urls import reverse

from taiga.base.utils import json
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_project(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_status(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_swimlane(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_no_swimlane(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_project(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_status(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_swimlane(client):
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


def test_api_update_orders_in_bulk_invalid_affter_us_because_no_swimlane(client):
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
