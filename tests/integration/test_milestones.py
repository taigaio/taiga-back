# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from datetime import timedelta
from urllib.parse import quote

from django.urls import reverse
from django.utils import timezone

from taiga.base.utils import json

from .. import factories as f


pytestmark = pytest.mark.django_db


def test_update_milestone_with_userstories_list(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    sprint = f.MilestoneFactory.create(project=project, owner=user)
    f.PointsFactory.create(project=project, value=None)
    us = f.UserStoryFactory.create(project=project, owner=user)

    url = reverse("milestones-detail", args=[sprint.pk])

    form_data = {
        "name": "test",
        "user_stories": [{"id": us.id}]
    }

    client.login(user)
    response = client.json.patch(url, json.dumps(form_data))
    assert response.status_code == 200


def test_list_milestones_taiga_info_headers(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)

    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=True)
    f.MilestoneFactory.create(project=project, owner=user, closed=False)
    f.MilestoneFactory.create(owner=user, closed=False)

    url = reverse("milestones-list")

    client.login(project.owner)
    response1 = client.json.get(url)
    response2 = client.json.get(url, {"project": project.id})

    assert response1.status_code == 200
    assert "taiga-info-total-closed-milestones" in response1["access-control-expose-headers"]
    assert "taiga-info-total-opened-milestones" in response1["access-control-expose-headers"]
    assert response1.has_header("Taiga-Info-Total-Closed-Milestones") == False
    assert response1.has_header("Taiga-Info-Total-Opened-Milestones") == False

    assert response2.status_code == 200
    assert "taiga-info-total-closed-milestones" in response2["access-control-expose-headers"]
    assert "taiga-info-total-opened-milestones" in response2["access-control-expose-headers"]
    assert response2.has_header("Taiga-Info-Total-Closed-Milestones") == True
    assert response2.has_header("Taiga-Info-Total-Opened-Milestones") == True
    assert response2["taiga-info-total-closed-milestones"] == "3"
    assert response2["taiga-info-total-opened-milestones"] == "1"


def test_api_filter_by_created_date__lte(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    one_day_ago = timezone.now() - timedelta(days=1)

    old_milestone = f.MilestoneFactory.create(
        project=project, owner=user, created_date=one_day_ago
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)

    url = reverse("milestones-list") + "?created_date__lte=%s" % (
        quote(milestone.created_date.isoformat())
    )

    client.login(milestone.owner)
    response = client.get(url)
    number_of_milestones = len(response.data)

    assert response.status_code == 200
    assert number_of_milestones == 2


def test_api_filter_by_modified_date__gte(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    one_day_ago = timezone.now() - timedelta(days=1)

    older_milestone = f.MilestoneFactory.create(
        project=project, owner=user, created_date=one_day_ago
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)
    # we have to refresh as it slightly differs
    milestone.refresh_from_db()

    assert older_milestone.modified_date < milestone.modified_date

    url = reverse("milestones-list") + "?modified_date__gte=%s" % (
        quote(milestone.modified_date.isoformat())
    )

    client.login(milestone.owner)
    response = client.get(url)
    number_of_milestones = len(response.data)

    assert response.status_code == 200
    assert number_of_milestones == 1
    assert response.data[0]["slug"] == milestone.slug


@pytest.mark.parametrize("field_name", [
    "estimated_start", "estimated_finish"
])
def test_api_filter_by_milestone__estimated_start_and_end(client, field_name):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project)
    f.MembershipFactory.create(
        project=project, user=user, role=role, is_admin=True
    )
    milestone = f.MilestoneFactory.create(project=project, owner=user)

    assert hasattr(milestone, field_name)
    date = getattr(milestone, field_name)
    before = (date - timedelta(days=1)).isoformat()
    after = (date + timedelta(days=1)).isoformat()

    client.login(milestone.owner)

    expections = {
        field_name + "__gte=" + quote(before): 1,
        field_name + "__gte=" + quote(after): 0,
        field_name + "__lte=" + quote(before): 0,
        field_name + "__lte=" + quote(after): 1
    }

    for param, expection in expections.items():
        url = reverse("milestones-list") + "?" + param
        response = client.get(url)
        number_of_milestones = len(response.data)

        assert response.status_code == 200
        assert number_of_milestones == expection, param
        if number_of_milestones > 0:
            assert response.data[0]["slug"] == milestone.slug


def test_api_update_milestone_in_bulk_userstories(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    us1 = f.create_userstory(project=project, milestone=milestone1,
                             sprint_order=1)
    us2 = f.create_userstory(project=project, milestone=milestone1,
                             sprint_order=2)

    assert project.milestones.get(id=milestone1.id).user_stories.count() == 2

    url = reverse("milestones-move-userstories-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_stories": [{"us_id": us2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).user_stories.count() == 1
    assert project.milestones.get(id=milestone2.id).user_stories.count() == 1


def test_api_move_userstories_to_another_sprint(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    us1 = f.create_userstory(project=project, milestone=milestone1,
                             sprint_order=1)
    us2 = f.create_userstory(project=project, milestone=milestone1,
                             sprint_order=2)

    assert project.milestones.get(id=milestone1.id).user_stories.count() == 2

    url = reverse("milestones-move-userstories-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_stories": [{"us_id": us2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).user_stories.count() == 1
    assert project.milestones.get(id=milestone2.id).user_stories.count() == 1


def test_api_move_userstories_to_another_sprint_close_previous(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    closed_status = f.UserStoryStatusFactory.create(is_closed=True)
    us1 = f.create_userstory(project=project, milestone=milestone1,
                             sprint_order=1, status=closed_status)
    us2 = f.create_userstory(project=project, milestone=milestone1, sprint_order=2)

    assert milestone1.user_stories.count() == 2
    assert not milestone1.closed

    url = reverse("milestones-move-userstories-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_stories": [{"us_id": us2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).user_stories.count() == 1
    assert project.milestones.get(id=milestone2.id).user_stories.count() == 1
    assert project.milestones.get(id=milestone1.id).closed


def test_api_move_tasks_to_another_sprint(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    task1 = f.create_task(project=project, milestone=milestone1, taskboard_order=1)
    task2 = f.create_task(project=project, milestone=milestone1, taskboard_order=2)

    assert project.milestones.get(id=milestone1.id).tasks.count() == 2

    url = reverse("milestones-move-tasks-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_tasks": [{"task_id": task2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).tasks.count() == 1
    assert project.milestones.get(id=milestone2.id).tasks.count() == 1


def test_api_move_tasks_to_another_sprint_close_previous(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    closed_status = f.TaskStatusFactory.create(project=project, is_closed=True)

    task1 = f.create_task(project=project, milestone=milestone1, taskboard_order=1,
                          status=closed_status, user_story=None)
    task2 = f.create_task(project=project, milestone=milestone1, taskboard_order=2,
                          user_story=None)

    assert project.milestones.get(id=milestone1.id).tasks.count() == 2
    assert not milestone1.closed

    url = reverse("milestones-move-tasks-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_tasks": [{"task_id": task2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).tasks.count() == 1
    assert project.milestones.get(id=milestone2.id).tasks.count() == 1
    assert project.milestones.get(id=milestone1.id).closed


def test_api_move_issues_to_another_sprint(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    issue1 = f.create_issue(project=project, milestone=milestone1)
    issue2 = f.create_issue(project=project, milestone=milestone1)

    assert project.milestones.get(id=milestone1.id).issues.count() == 2

    url = reverse("milestones-move-issues-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_issues": [{"issue_id": issue2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).issues.count() == 1
    assert project.milestones.get(id=milestone2.id).issues.count() == 1


def test_api_move_issues_to_another_sprint_close_previous(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner,
                               is_admin=True)
    milestone1 = f.MilestoneFactory.create(project=project)
    milestone2 = f.MilestoneFactory.create(project=project)

    closed_status = f.IssueStatusFactory.create(project=project,
                                                is_closed=True)
    issue1 = f.create_issue(project=project, milestone=milestone1,
                            status=closed_status)
    issue2 = f.create_issue(project=project, milestone=milestone1)

    assert project.milestones.get(id=milestone1.id).closed is False
    assert project.milestones.get(id=milestone1.id).issues.count() == 2

    url = reverse("milestones-move-issues-to-sprint", kwargs={"pk": milestone1.pk})
    data = {
        "project_id": project.id,
        "milestone_id": milestone2.id,
        "bulk_issues": [{"issue_id": issue2.id, "order": 2}]
    }
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone1.id).issues.count() == 1
    assert project.milestones.get(id=milestone2.id).issues.count() == 1
    assert project.milestones.get(id=milestone1.id).closed
