# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.tasks import services

from .. import factories as f

import pytest
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


def test_create_tasks_in_bulk(db):
    data = """
Task #1
Task #2
"""
    with mock.patch("taiga.projects.tasks.services.db") as db:
        tasks = services.create_tasks_in_bulk(data)
        db.save_in_bulk.assert_called_once_with(tasks, None, None)


def test_create_task_without_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    status = f.TaskStatusFactory.create(project=project)
    project.default_task_status = status
    project.save()

    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("tasks-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] == project.default_task_status.id


def test_create_task_without_default_values(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("tasks-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] == None


def test_api_create_in_bulk_with_status_milestone_userstory(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory(project=project)
    us = f.create_userstory(project=project, milestone=milestone)

    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "us_id": us.id,
        "project_id": us.project.id,
        "milestone_id": us.milestone.id,
        "status_id": us.project.default_task_status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data[0]["status"] == us.project.default_task_status.id


def test_api_create_in_bulk_with_status_milestone(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory(project=project)
    us = f.create_userstory(project=project, milestone=milestone)

    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "project_id": us.project.id,
        "milestone_id": us.milestone.id,
        "status_id": us.project.default_task_status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data[0]["status"] == us.project.default_task_status.id


def test_api_create_in_bulk_with_invalid_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory(project=project)
    us = f.create_userstory(project=project, milestone=milestone)

    status = f.TaskStatusFactory.create()


    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "us_id": us.id,
        "project_id": project.id,
        "milestone_id": milestone.id,
        "status_id": status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "status_id" in response.data


def test_api_create_in_bulk_with_invalid_milestone(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory()
    us = f.create_userstory(project=project)

    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "us_id": us.id,
        "project_id": project.id,
        "milestone_id": milestone.id,
        "status_id": project.default_task_status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "milestone_id" in response.data


def test_api_create_in_bulk_with_invalid_userstory_1(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory(project=project)
    us = f.create_userstory()

    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "us_id": us.id,
        "project_id": project.id,
        "milestone_id": milestone.id,
        "status_id": project.default_task_status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "us_id" in response.data


def test_api_create_in_bulk_with_invalid_userstory_2(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    milestone = f.MilestoneFactory(project=project)
    us = f.create_userstory(project=project)

    url = reverse("tasks-bulk-create")
    data = {
        "bulk_tasks": "Story #1\nStory #2",
        "us_id": us.id,
        "project_id": us.project.id,
        "milestone_id": milestone.id,
        "status_id": us.project.default_task_status.id
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "us_id" in response.data


def test_api_create_invalid_task(client):
    # Associated to a milestone and a user story.
    # But the User Story is not associated with the milestone
    us_milestone = f.MilestoneFactory.create()
    us = f.create_userstory(milestone=us_milestone)
    f.MembershipFactory.create(project=us.project, user=us.owner, is_admin=True)
    us.project.default_task_status = f.TaskStatusFactory.create(project=us.project)
    task_milestone = f.MilestoneFactory.create(project=us.project, owner=us.owner)

    url = reverse("tasks-list")
    data = {
        "user_story": us.id,
        "milestone": task_milestone.id,
        "subject": "Testing subject",
        "status": us.project.default_task_status.id,
        "project": us.project.id
    }

    client.login(us.owner)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_api_update_order_in_bulk(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2}]
    }

    client.login(project.owner)

    response1 = client.json.post(url1, json.dumps(data))
    response2 = client.json.post(url2, json.dumps(data))

    assert response1.status_code == 200, response1.data
    assert response2.status_code == 200, response2.data


def test_api_update_order_in_bulk_invalid_tasks(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task()

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data



def test_api_update_order_in_bulk_invalid_tasks_for_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project, status=task1.status)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "status_id": task1.status.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_tasks_for_milestone(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    mil1 = f.MilestoneFactory.create(project=project)
    task1 = f.create_task(project=project, milestone=mil1)
    task2 = f.create_task(project=project, milestone=mil1)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "milestone_id": mil1.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_tasks_for_user_story(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project)
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "us_id": us1.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status = f.TaskStatusFactory.create()
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "status_id": status.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "status_id" in response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "status_id" in response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_milestone(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    mil1 = f.MilestoneFactory.create()
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "milestone_id": mil1.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "milestone_id" in response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "milestone_id" in response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_user_story_1(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory()
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "us_id": us1.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "us_id" in response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "us_id" in response.data
    assert "bulk_tasks" in response.data


def test_api_update_order_in_bulk_invalid_user_story_2(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    milestone = f.MilestoneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    task1 = f.create_task(project=project)
    task2 = f.create_task(project=project)
    task3 = f.create_task(project=project)

    url1 = reverse("tasks-bulk-update-taskboard-order")
    url2 = reverse("tasks-bulk-update-us-order")

    data = {
        "project_id": project.id,
        "us_id": us1.id,
        "milestone_id": milestone.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url1, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "us_id" in response.data
    assert "bulk_tasks" in response.data

    response = client.json.post(url2, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "us_id" in response.data
    assert "bulk_tasks" in response.data


def test_get_invalid_csv(client):
    url = reverse("tasks-csv")

    response = client.get(url)
    assert response.status_code == 404

    response = client.get("{}?uuid={}".format(url, "not-valid-uuid"))
    assert response.status_code == 404


def test_get_valid_csv(client):
    url = reverse("tasks-csv")
    project = f.ProjectFactory.create(tasks_csv_uuid=uuid.uuid4().hex)

    response = client.get("{}?uuid={}".format(url, project.tasks_csv_uuid))
    assert response.status_code == 200


def test_custom_fields_csv_generation():
    project = f.ProjectFactory.create(tasks_csv_uuid=uuid.uuid4().hex)
    attr = f.TaskCustomAttributeFactory.create(project=project, name="attr1", description="desc")
    task = f.TaskFactory.create(project=project)
    attr_values = task.custom_attributes_values
    attr_values.attributes_values = {str(attr.id):"val1"}
    attr_values.save()
    queryset = project.tasks.all()
    data = services.tasks_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)
    assert row[24] == attr.name
    row = next(reader)
    assert row[24] == "val1"


def test_get_tasks_including_attachments(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    task = f.TaskFactory.create(project=project)
    f.TaskAttachmentFactory(project=project, content_object=task)
    url = reverse("tasks-list")

    client.login(project.owner)

    response = client.get(url)
    assert response.status_code == 200
    assert response.data[0].get("attachments") == []

    url = reverse("tasks-list") + "?include_attachments=1"
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data[0].get("attachments")) == 1


def test_api_filter_by_created_date(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    old_task = f.create_task(owner=user, created_date=one_day_ago)
    task = f.create_task(owner=user, subject="test")

    url = reverse("tasks-list") + "?created_date=%s" % (
        quote(task.created_date.isoformat())
    )

    client.login(task.owner)
    response = client.get(url)
    number_of_tasks = len(response.data)

    assert response.status_code == 200
    assert number_of_tasks == 1
    assert response.data[0]["subject"] == task.subject


def test_api_filter_by_created_date__lt(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    old_task = f.create_task(owner=user, created_date=one_day_ago)
    task = f.create_task(owner=user, subject="test")

    url = reverse("tasks-list") + "?created_date__lt=%s" % (
        quote(task.created_date.isoformat())
    )

    client.login(task.owner)
    response = client.get(url)
    number_of_tasks = len(response.data)

    assert response.status_code == 200
    assert response.data[0]["subject"] == old_task.subject


def test_api_filter_by_created_date__lte(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    old_task = f.create_task(owner=user, created_date=one_day_ago)
    task = f.create_task(owner=user)

    url = reverse("tasks-list") + "?created_date__lte=%s" % (
        quote(task.created_date.isoformat())
    )

    client.login(task.owner)
    response = client.get(url)
    number_of_tasks = len(response.data)

    assert response.status_code == 200
    assert number_of_tasks == 2


def test_api_filter_by_modified_date__gte(client):
    user = f.UserFactory(is_superuser=True)
    _day_ago = datetime.now(pytz.utc) - timedelta(days=1)

    older_task = f.create_task(owner=user)
    task = f.create_task(owner=user, subject="test")
    # we have to refresh as it slightly differs
    task.refresh_from_db()

    assert older_task.modified_date < task.modified_date

    url = reverse("tasks-list") + "?modified_date__gte=%s" % (
        quote(task.modified_date.isoformat())
    )

    client.login(task.owner)
    response = client.get(url)
    number_of_tasks = len(response.data)

    assert response.status_code == 200
    assert number_of_tasks == 1
    assert response.data[0]["subject"] == task.subject


def test_api_filter_by_finished_date(client):
    user = f.UserFactory(is_superuser=True)
    project = f.ProjectFactory.create()
    status0 = f.TaskStatusFactory.create(project=project, is_closed=True)

    task = f.create_task(owner=user)
    finished_task = f.create_task(owner=user, status=status0, subject="test")

    assert finished_task.finished_date

    url = reverse("tasks-list") + "?finished_date__gte=%s" % (
        quote(finished_task.finished_date.isoformat())
    )
    client.login(task.owner)
    response = client.get(url)
    number_of_tasks = len(response.data)

    assert response.status_code == 200
    assert number_of_tasks == 1
    assert response.data[0]["subject"] == finished_task.subject


def test_api_filters_data(client):
    project = f.ProjectFactory.create()
    user1 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user1, project=project)
    user2 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user2, project=project)
    user3 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user3, project=project)

    status0 = f.TaskStatusFactory.create(project=project)
    status1 = f.TaskStatusFactory.create(project=project)
    status2 = f.TaskStatusFactory.create(project=project)
    status3 = f.TaskStatusFactory.create(project=project)

    tag0 = "test1test2test3"
    tag1 = "test1"
    tag2 = "test2"
    tag3 = "test3"

    # ------------------------------------------------------
    # | Task  |  Owner | Assigned To | Tags                |
    # |-------#--------#-------------#---------------------|
    # | 0     |  user2 | None        |      tag1           |
    # | 1     |  user1 | None        |           tag2      |
    # | 2     |  user3 | None        |      tag1 tag2      |
    # | 3     |  user2 | None        |                tag3 |
    # | 4     |  user1 | user1       |      tag1 tag2 tag3 |
    # | 5     |  user3 | user1       |                tag3 |
    # | 6     |  user2 | user1       |      tag1 tag2      |
    # | 7     |  user1 | user2       |                tag3 |
    # | 8     |  user3 | user2       |      tag1           |
    # | 9     |  user2 | user3       | tag0                |
    # ------------------------------------------------------

    task0 = f.TaskFactory.create(project=project, owner=user2, assigned_to=None,
                                            status=status3, tags=[tag1])
    task1 = f.TaskFactory.create(project=project, owner=user1, assigned_to=None,
                                            status=status3, tags=[tag2])
    task2 = f.TaskFactory.create(project=project, owner=user3, assigned_to=None,
                                            status=status1, tags=[tag1, tag2])
    task3 = f.TaskFactory.create(project=project, owner=user2, assigned_to=None,
                                            status=status0, tags=[tag3])
    task4 = f.TaskFactory.create(project=project, owner=user1, assigned_to=user1,
                                            status=status0, tags=[tag1, tag2, tag3])
    task5 = f.TaskFactory.create(project=project, owner=user3, assigned_to=user1,
                                            status=status2, tags=[tag3])
    task6 = f.TaskFactory.create(project=project, owner=user2, assigned_to=user1,
                                            status=status3, tags=[tag1, tag2])
    task7 = f.TaskFactory.create(project=project, owner=user1, assigned_to=user2,
                                            status=status0, tags=[tag3])
    task8 = f.TaskFactory.create(project=project, owner=user3, assigned_to=user2,
                                            status=status3, tags=[tag1])
    task9 = f.TaskFactory.create(project=project, owner=user2, assigned_to=user3,
                                            status=status1, tags=[tag0])

    url = reverse("tasks-filters-data") + "?project={}".format(project.id)

    client.login(user1)

    ## No filter
    response = client.get(url)
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 4
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 3

    assert next(filter(lambda i: i['id'] == None, response.data["assigned_to"]))["count"] == 4
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 4

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 1
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 5
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 4
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 4

    ## Filter ((status0 or status3)
    response = client.get(url + "&status={},{}".format(status3.id, status0.id))
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == None, response.data["assigned_to"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 0

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 4

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 0
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 4
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 3
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 3

    ## Filter ((tag1 and tag2) and (user1 or user2))
    response = client.get(url + "&tags={},{}&owner={},{}".format(tag1, tag2, user1.id, user2.id))
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == None, response.data["assigned_to"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 0

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 1

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 0
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 2
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 2
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 1
