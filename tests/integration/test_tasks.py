# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid
import csv

from datetime import timedelta
from urllib.parse import quote

from unittest import mock

from django.urls import reverse
from django.utils import timezone

from taiga.base.utils import json
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.occ import OCCResourceMixin
from taiga.projects.tasks import services
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.votes.services import add_vote

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def create_tasks_fixtures():
    data = {}
    data["project"] = f.ProjectFactory.create()
    project = data["project"]
    data["users"] = [f.UserFactory.create(is_superuser=True) for i in range(0, 3)]
    data["roles"] = [f.RoleFactory.create() for i in range(0, 3)]
    user_roles = zip(data["users"], data["roles"])
    # Add membership fixtures
    [f.MembershipFactory.create(user=user, project=project, role=role) for (user, role) in user_roles]

    data["statuses"] = [f.TaskStatusFactory.create(project=project) for i in range(0, 4)]
    data["tags"] = ["test1test2test3", "test1", "test2", "test3"]

    # ----------------------------------------------------------------
    # | Task  |  Owner | Assigned To | Tags                | Status  |
    # |-------#--------#-------------#---------------------|---------|
    # | 0     |  user2 | None        |      tag1           | status3 |
    # | 1     |  user1 | None        |           tag2      | status3 |
    # | 2     |  user3 | None        |      tag1 tag2      | status1 |
    # | 3     |  user2 | None        |                tag3 | status0 |
    # | 4     |  user1 | user1       |      tag1 tag2 tag3 | status0 |
    # | 5     |  user3 | user1       |                tag3 | status2 |
    # | 6     |  user2 | user1       |      tag1 tag2      | status3 |
    # | 7     |  user1 | user2       |                tag3 | status0 |
    # | 8     |  user3 | user2       |      tag1           | status3 |
    # | 9     |  user2 | user3       | tag0                | status1 |
    # ----------------------------------------------------------------

    (user1, user2, user3, ) = data["users"]
    (status0, status1, status2, status3 ) = data["statuses"]
    (tag0, tag1, tag2, tag3, ) = data["tags"]

    f.TaskFactory.create(project=project, owner=user2, assigned_to=None,
                                            status=status3, tags=[tag1])
    f.TaskFactory.create(project=project, owner=user1, assigned_to=None,
                                            status=status3, tags=[tag2])
    f.TaskFactory.create(project=project, owner=user3, assigned_to=None,
                                            status=status1, tags=[tag1, tag2])
    f.TaskFactory.create(project=project, owner=user2, assigned_to=None,
                                            status=status0, tags=[tag3])
    f.TaskFactory.create(project=project, owner=user1, assigned_to=user1,
                                            status=status0, tags=[tag1, tag2, tag3])
    f.TaskFactory.create(project=project, owner=user3, assigned_to=user1,
                                            status=status2, tags=[tag3])
    f.TaskFactory.create(project=project, owner=user2, assigned_to=user1,
                                            status=status3, tags=[tag1, tag2])
    f.TaskFactory.create(project=project, owner=user1, assigned_to=user2,
                                            status=status0, tags=[tag3])
    f.TaskFactory.create(project=project, owner=user3, assigned_to=user2,
                                            status=status3, tags=[tag1])
    f.TaskFactory.create(project=project, owner=user2, assigned_to=user3,
                                            status=status1, tags=[tag0])

    return data


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


def test_api_update_milestone_in_bulk(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    milestone1 = f.MilestoneFactory(project=project)
    milestone2 = f.MilestoneFactory(project=project)
    task1 = f.create_task(project=project, milestone=milestone1)
    task2 = f.create_task(project=project, milestone=milestone1)
    task3 = f.create_task(project=project, milestone=milestone1)

    url = reverse("tasks-bulk-update-milestone")

    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data
    assert response.data[task1.id] == milestone2.id
    assert response.data[task2.id] == milestone2.id
    assert response.data[task3.id] == milestone2.id


def test_api_update_milestone_in_bulk_invalid_milestone(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_task_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    milestone1 = f.MilestoneFactory(project=project)
    milestone2 = f.MilestoneFactory()
    task1 = f.create_task(project=project, milestone=milestone1)
    task2 = f.create_task(project=project, milestone=milestone1)
    task3 = f.create_task(project=project, milestone=milestone1)

    url = reverse("tasks-bulk-update-milestone")

    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_tasks": [{"task_id": task1.id, "order": 1},
                       {"task_id": task2.id, "order": 2},
                       {"task_id": task3.id, "order": 3}]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "milestone_id" in response.data


def test_get_invalid_csv(client):
    url = reverse("tasks-csv")
    project = f.ProjectFactory.create(tasks_csv_uuid=uuid.uuid4().hex)
    client.login(project.owner)

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
    assert row[28] == attr.name
    row = next(reader)
    assert row[28] == "val1"


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
    one_day_ago = timezone.now() - timedelta(days=1)

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
    one_day_ago = timezone.now() - timedelta(days=1)

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
    one_day_ago = timezone.now() - timedelta(days=1)

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
    _day_ago = timezone.now() - timedelta(days=1)

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


@pytest.mark.parametrize("field_name", ["estimated_start", "estimated_finish"])
def test_api_filter_by_milestone__estimated_start_and_end(client, field_name):
    user = f.UserFactory(is_superuser=True)
    task = f.create_task(owner=user)

    assert task.milestone
    assert hasattr(task.milestone, field_name)
    date = getattr(task.milestone, field_name)
    before = (date - timedelta(days=1)).isoformat()
    after = (date + timedelta(days=1)).isoformat()

    client.login(task.owner)

    full_field_name = "milestone__" + field_name
    expections = {
        full_field_name + "__gte=" + quote(before): 1,
        full_field_name + "__gte=" + quote(after): 0,
        full_field_name + "__lte=" + quote(before): 0,
        full_field_name + "__lte=" + quote(after): 1
    }

    for param, expection in expections.items():
        url = reverse("tasks-list") + "?" + param
        response = client.get(url)
        number_of_tasks = len(response.data)

        assert response.status_code == 200
        assert number_of_tasks == expection, param
        if number_of_tasks > 0:
            assert response.data[0]["subject"] == task.subject


@pytest.mark.parametrize("filter_name,collection,expected,exclude_expected,is_text", [
    ('status', 'statuses', 3, 7, False),
    ('assigned_to', 'users', 3, 7, False),
    ('tags', 'tags', 1, 9, True),
    ('owner', 'users', 3, 7, False),
    ('role', 'roles', 3, 7, False),
])
def test_api_filters(client, filter_name, collection, expected, exclude_expected, is_text):
    data = create_tasks_fixtures()
    project = data["project"]
    options = data[collection]

    client.login(data["users"][0])
    if is_text:
        param = options[0]
    else:
        param = options[0].id

    # include test
    url = "{}?project={}&{}={}".format(reverse('tasks-list'), project.id, filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == expected

    # exclude test
    url = "{}?project={}&exclude_{}={}".format(reverse('tasks-list'), project.id, filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == exclude_expected


def test_api_filters_tags_or_operator(client):
    data = create_tasks_fixtures()
    project = data["project"]
    client.login(data["users"][0])
    tags = data["tags"]

    url = "{}?project={}&tags={},{}".format(reverse('tasks-list'), project.id, tags[0], tags[2])
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 5


def test_api_filters_data(client):
    data = create_tasks_fixtures()
    project = data["project"]
    (user1, user2, user3, ) = data["users"]
    (status0, status1, status2, status3, ) = data["statuses"]
    (tag0, tag1, tag2, tag3, ) = data["tags"]

    url = reverse("tasks-filters-data") + "?project={}".format(project.id)
    client.login(user1)

    ## No filter
    response = client.get(url)
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 4
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 3

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 4
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

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 3
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

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 2

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 0

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 3

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 1
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 3
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 3
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 3


def test_api_validator_assigned_to_when_update_tasks(client):
    project = f.create_project(anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                               public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)))
    project_member_owner = f.MembershipFactory.create(project=project,
                                                      user=project.owner,
                                                      is_admin=True,
                                                      role__project=project,
                                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_member = f.MembershipFactory.create(project=project,
                                                is_admin=True,
                                                role__project=project,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_no_member = f.MembershipFactory.create(is_admin=True)

    task = f.create_task(project=project, milestone__project=project, user_story=None, owner=project.owner)

    url = reverse('tasks-detail', kwargs={"pk": task.pk})

    # assign
    data = {
        "assigned_to": project_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 200, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == project_member.user.id

    # unassign
    data = {
        "assigned_to": None,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 200, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == None

    # assign to invalid user
    data = {
        "assigned_to": project_no_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 400, response.data


def test_api_validator_assigned_to_when_create_tasks(client):
    project = f.create_project(anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                               public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)))
    project_member_owner = f.MembershipFactory.create(project=project,
                                                      user=project.owner,
                                                      is_admin=True,
                                                      role__project=project,
                                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_member = f.MembershipFactory.create(project=project,
                                                is_admin=True,
                                                role__project=project,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_no_member = f.MembershipFactory.create(is_admin=True)

    url = reverse('tasks-list')

    # assign
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": project_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == project_member.user.id

    # unassign
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": None,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == None

    # assign to invalid user
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": project_no_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 400, response.data


def test_promote_task_to_us(client):
    user_1 = f.UserFactory.create()
    user_2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user_1)
    f.MembershipFactory.create(project=project, user=user_1, is_admin=True)
    f.MembershipFactory.create(project=project, user=user_2, is_admin=False)
    task = f.TaskFactory.create(project=project, owner=user_1, assigned_to=user_2)
    task.add_watcher(user_1)
    task.add_watcher(user_2)
    add_vote(task, user_1)
    add_vote(task, user_2)

    f.TaskAttachmentFactory(project=project, content_object=task, owner=user_1)

    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": user_1.id},
        comment="Test comment",
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[],
    )

    f.HistoryEntryFactory.create(
        project=project,
        user={"pk": user_2.id},
        comment="Test comment 2",
        key="tasks.task:{}".format(task.id),
        is_hidden=False,
        diff=[]
    )

    client.login(user_1)

    url = reverse('tasks-promote-to-user-story', kwargs={"pk": task.pk})
    data = {"project_id": project.id}
    promote_response = client.json.post(url, json.dumps(data))

    us_ref = promote_response.data.pop()
    us = UserStory.objects.get(ref=us_ref)
    us_response = client.get(reverse("userstories-detail", args=[us.pk]),
                             {"include_attachments": True})

    assert promote_response.status_code == 200, promote_response.data
    assert us_response.data["subject"] == task.subject
    assert us_response.data["description"] == task.description
    assert us_response.data["owner"] == task.owner_id
    assert us_response.data["generated_from_task"] == None
    assert us_response.data["assigned_users"] == {user_2.id}
    assert us_response.data["total_watchers"] == 2
    assert us_response.data["total_attachments"] == 1
    assert us_response.data["total_comments"] == 2
    assert us_response.data["due_date"] == task.due_date
    assert us_response.data["is_blocked"] == task.is_blocked
    assert us_response.data["blocked_note"] == task.blocked_note
    assert us_response.data["total_voters"] == 2

    # check if task is deleted
    assert us_response.data["from_task_ref"] == us.from_task_ref
    assert not Task.objects.filter(pk=task.id).exists()
