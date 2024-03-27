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
from taiga.projects.userstories import services, models

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db(transaction=True)


def create_uss_fixtures():
    data = {}

    data["project"] = f.ProjectFactory.create()
    project = data["project"]
    data["users"] = [f.UserFactory.create(is_superuser=True) for i in range(0, 3)]
    data["roles"] = [f.RoleFactory.create() for i in range(0, 3)]
    user_roles = zip(data["users"], data["roles"])
    # Add membership fixtures
    [f.MembershipFactory.create(user=user, project=project, role=role) for (user, role) in user_roles]

    data["statuses"] = [f.UserStoryStatusFactory.create(project=project) for i in range(0, 4)]
    data["epics"] = [f.EpicFactory.create(project=project) for i in range(0, 3)]
    data["tags"] = ["test1test2test3", "test1", "test2", "test3"]

    # --------------------------------------------------------------------------------------------------------
    # | US | Status  |  Owner | Assigned To | Assigned Users | Tags                | Epic        | Milestone |
    # |----#---------#--------#-------------#----------------#---------------------#--------------------------
    # | 0  | status3 |  user2 | None        | None           |      tag1           | epic0       | None      |
    # | 1  | status3 |  user1 | None        | user1          |           tag2      | None        |           |
    # | 2  | status1 |  user3 | None        | None           |      tag1 tag2      | epic1       | None      |
    # | 3  | status0 |  user2 | None        | None           |                tag3 | None        |           |
    # | 4  | status0 |  user1 | user1       | None           |      tag1 tag2 tag3 | epic0       | None      |
    # | 5  | status2 |  user3 | user1       | None           |                tag3 | None        |           |
    # | 6  | status3 |  user2 | user1       | None           |      tag1 tag2      | epic0 epic2 | None      |
    # | 7  | status0 |  user1 | user2       | None           |                tag3 | None        |           |
    # | 8  | status3 |  user3 | user2       | None           |      tag1           | epic2       | None      |
    # | 9  | status1 |  user2 | user3       | user1          | tag0                | None        |           |
    # --------------------------------------------------------------------------------------------------------

    (user1, user2, user3, ) = data["users"]
    (status0, status1, status2, status3 ) = data["statuses"]
    (epic0, epic1, epic2) = data["epics"]
    (tag0, tag1, tag2, tag3, ) = data["tags"]

    us0 = f.UserStoryFactory.create(project=project, owner=user2, assigned_to=None,
                              status=status3, tags=[tag1], milestone=None)
    f.RelatedUserStory.create(user_story=us0, epic=epic0)
    us1 = f.UserStoryFactory.create(project=project, owner=user1, assigned_to=None,
                              status=status3, tags=[tag2], assigned_users=[user1])
    us2 = f.UserStoryFactory.create(project=project, owner=user3, assigned_to=None,
                              status=status1, tags=[tag1, tag2], milestone=None)
    f.RelatedUserStory.create(user_story=us2, epic=epic1)
    us3 = f.UserStoryFactory.create(project=project, owner=user2, assigned_to=None,
                              status=status0, tags=[tag3])
    us4 = f.UserStoryFactory.create(project=project, owner=user1, assigned_to=user1,
                              status=status0, tags=[tag1, tag2, tag3], milestone=None)
    f.RelatedUserStory.create(user_story=us4, epic=epic0)
    us5 = f.UserStoryFactory.create(project=project, owner=user3, assigned_to=user1,
                              status=status2, tags=[tag3])
    us6 = f.UserStoryFactory.create(project=project, owner=user2, assigned_to=user1,
                              status=status3, tags=[tag1, tag2], milestone=None)
    f.RelatedUserStory.create(user_story=us6, epic=epic0)
    f.RelatedUserStory.create(user_story=us6, epic=epic2)
    us7 = f.UserStoryFactory.create(project=project, owner=user1, assigned_to=user2,
                              status=status0, tags=[tag3])
    us8 = f.UserStoryFactory.create(project=project, owner=user3, assigned_to=user2,
                              status=status3, tags=[tag1], milestone=None)
    f.RelatedUserStory.create(user_story=us8, epic=epic2)
    us9 = f.UserStoryFactory.create(project=project, owner=user2, assigned_to=user3,
                              status=status1, tags=[tag0], assigned_users=[user1])

    data["userstories"] = [us0, us1, us2, us3, us4, us5, us6, us7, us8, us9]

    return data


def test_get_userstories_from_bulk():
    data = "User Story #1\nUser Story #2\n"
    userstories = services.get_userstories_from_bulk(data)

    assert len(userstories) == 2
    assert userstories[0].subject == "User Story #1"
    assert userstories[1].subject == "User Story #2"


def test_create_userstories_in_bulk():
    data = "User Story #1\nUser Story #2\n"
    project = f.ProjectFactory.create()

    with mock.patch("taiga.projects.userstories.services.db") as db:
        userstories = services.create_userstories_in_bulk(data, project=project)
        db.save_in_bulk.assert_called_once_with(userstories, None, None)


def test_update_userstories_order_in_bulk():
    project = f.ProjectFactory.create()
    us1 = f.UserStoryFactory.create(project=project, backlog_order=1)
    us2 = f.UserStoryFactory.create(project=project, backlog_order=2)
    data = [{"us_id": us1.id, "order": 2}, {"us_id": us2.id, "order": 1}]

    with mock.patch("taiga.projects.userstories.services.db") as db:
        services.update_userstories_order_in_bulk(data, "backlog_order", project)
        db.update_attr_in_bulk_for_ids.assert_called_once_with({us2.id: 1, us1.id: 2},
                                                                "backlog_order",
                                                                models.UserStory)


def test_create_userstory_with_assign_to(client):
    user = f.UserFactory.create()
    user_watcher = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.MembershipFactory.create(project=project, user=user_watcher,
                               is_admin=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id,
            "assigned_to": user.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert response.data["assigned_to"] == user.id


def test_create_userstory_with_assigned_users(client):
    user = f.UserFactory.create()
    user_watcher = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.MembershipFactory.create(project=project, user=user_watcher,
                               is_admin=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id,
            "assigned_users": [user.id, user_watcher.id]}
    client.login(user)
    json_data = json.dumps(data)

    response = client.json.post(url, json_data)

    assert response.status_code == 201
    assert response.data["assigned_users"] == set([user.id, user_watcher.id])


def test_create_userstory_with_watchers(client):
    user = f.UserFactory.create()
    user_watcher = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.MembershipFactory.create(project=project, user=user_watcher, is_admin=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id, "watchers": [user_watcher.id]}
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert response.data["watchers"] == []


def test_create_userstory_without_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    status = f.UserStoryStatusFactory.create(project=project)
    project.default_us_status = status
    project.save()

    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] == project.default_us_status.id


def test_create_userstory_without_default_values(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, default_us_status=None)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    url = reverse("userstories-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] is None


def test_api_delete_userstory(client):
    us = f.UserStoryFactory.create()
    f.MembershipFactory.create(project=us.project, user=us.owner, is_admin=True)
    url = reverse("userstories-detail", kwargs={"pk": us.pk})

    client.login(us.owner)
    response = client.delete(url)

    assert response.status_code == 204


def test_api_filter_by_subject_or_ref(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    f.UserStoryFactory.create(project=project)
    f.UserStoryFactory.create(project=project, subject="some random subject")
    url = reverse("userstories-list") + "?q=some subject"

    client.login(project.owner)
    response = client.get(url)
    number_of_stories = len(response.data)

    assert response.status_code == 200
    assert number_of_stories == 1, number_of_stories


def test_api_create_in_bulk_with_status(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
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


def test_api_create_in_bulk_with_invalid_status(client):
    project = f.create_project()
    status = f.UserStoryStatusFactory.create()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    url = reverse("userstories-bulk-create")
    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "status_id": status.id
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400, response.data
    assert "status_id" in response.data


def test_api_create_in_bulk_with_swimlane(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    swimlane = f.create_swimlane(project=project)
    url = reverse("userstories-bulk-create")
    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "swimlane_id": project.default_swimlane_id,
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data
    assert response.data[1]["swimlane"] == project.default_swimlane_id


def test_api_create_in_bulk_with_invalid_swimlane(client):
    project = f.create_project()
    swimlane = f.create_swimlane()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    url = reverse("userstories-bulk-create")
    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "swimlane_id": swimlane.id,
    }

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400, response.data
    assert "swimlane_id" in response.data


def test_api_create_in_bulk_with_swimlane_unassigned(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    url = reverse("userstories-bulk-create")

    client.login(project.owner)

    data = {
        "bulk_stories": "Story #1\nStory #2",
        "project_id": project.id,
        "swimlane_id": None,
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data
    assert response.data[1]["swimlane"] == None


def test_api_update_milestone_in_bulk(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    milestone = f.MilestoneFactory.create(project=project)
    us1 = f.create_userstory(project=project)
    t1 = f.create_task(user_story=us1, project=project)
    t2 = f.create_task(user_story=us1, project=project)
    us2 = f.create_userstory(project=project)
    t3 = f.create_task(user_story=us2, project=project)
    us3 = f.create_userstory(project=project, milestone=milestone, sprint_order=1)
    us4 = f.create_userstory(project=project, milestone=milestone, sprint_order=2)

    url = reverse("userstories-bulk-update-milestone")
    data = {
        "project_id": project.id,
        "milestone_id": milestone.id,
        "bulk_stories": [{"us_id": us1.id, "order": 2},
                         {"us_id": us2.id, "order": 3}]
    }

    client.login(project.owner)

    assert project.milestones.get(id=milestone.id).user_stories.count() == 2
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 204, response.data
    assert project.milestones.get(id=milestone.id).user_stories.count() == 4

    uss_list = list(project.milestones.get(id=milestone.id).user_stories.order_by("sprint_order")
                                                                        .values_list("id", "sprint_order"))
    assert uss_list == [(us3.id, 1), (us1.id, 2), (us2.id,3), (us4.id,4)]

    tasks_list = list(project.milestones.get(id=milestone.id).tasks.order_by("id")
                                                                   .values_list("id", flat=True))
    assert tasks_list == [t1.id, t2.id, t3.id]


def test_api_update_milestone_in_bulk_invalid_milestone(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    m2 = f.MilestoneFactory.create()

    url = reverse("userstories-bulk-update-milestone")
    data = {
        "project_id": project.id,
        "milestone_id": m2.id,
        "bulk_stories": [{"us_id": us1.id, "order": 1},
                         {"us_id": us2.id, "order": 2}]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "milestone_id" in response.data


def test_api_update_milestone_in_bulk_invalid_userstories(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory()
    milestone = f.MilestoneFactory.create(project=project)

    url = reverse("userstories-bulk-update-milestone")
    data = {
        "project_id": project.id,
        "milestone_id": milestone.id,
        "bulk_stories": [{"us_id": us1.id, "order": 1},
                         {"us_id": us2.id, "order": 2}]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "bulk_stories" in response.data


def test_update_userstory_points(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    f.MembershipFactory.create(project=project, user=user1, role=role1, is_admin=True)
    f.MembershipFactory.create(project=project, user=user2, role=role2)

    points1 = f.PointsFactory.create(project=project, value=None)
    points2 = f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    us = f.create_userstory(project=project, owner=user1, status__project=project,
                            milestone__project=project)

    url = reverse("userstories-detail", args=[us.pk])

    client.login(user1)

    # invalid role
    data = {
        "version": us.version,
        "points": {
            str(role1.pk): points1.pk,
            str(role2.pk): points2.pk,
            "222222": points3.pk
        }
    }

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    # invalid point
    data = {
        "version": us.version,
        "points": {
            str(role1.pk): 999999,
            str(role2.pk): points2.pk
        }
    }

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

    # Api should save successful
    data = {
        "version": us.version,
        "points": {
            str(role1.pk): points3.pk,
            str(role2.pk): points2.pk
        }
    }

    response = client.json.patch(url, json.dumps(data))
    assert response.data["points"][str(role1.pk)] == points3.pk


def test_update_userstory_rolepoints_on_add_new_role(client):
    # This test is explicitly without assertions. It simple should
    # works without raising any exception.

    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user1)

    role1 = f.RoleFactory.create(project=project)

    f.MembershipFactory.create(project=project, user=user1, role=role1)

    f.PointsFactory.create(project=project, value=2)

    us = f.UserStoryFactory.create(project=project, owner=user1)
    # url = reverse("userstories-detail", args=[us.pk])
    # client.login(user1)

    role2 = f.RoleFactory.create(project=project, computable=True)
    f.MembershipFactory.create(project=project, user=user2, role=role2)
    us.save()


def test_archived_filter(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.UserStoryFactory.create(project=project)
    archived_status = f.UserStoryStatusFactory.create(is_archived=True)
    f.UserStoryFactory.create(status=archived_status, project=project)

    client.login(user)

    url = reverse("userstories-list")

    data = {}
    response = client.get(url, data)
    assert len(response.data) == 2

    data = {"status__is_archived": 0}
    response = client.get(url, data)
    assert len(response.data) == 1

    data = {"status__is_archived": 1}
    response = client.get(url, data)
    assert len(response.data) == 1


def test_filter_by_multiple_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    f.UserStoryFactory.create(project=project)
    us1 = f.UserStoryFactory.create(project=project)
    us2 = f.UserStoryFactory.create(project=project)

    client.login(user)

    url = "{}?status={},{}".format(reverse("userstories-list"), us1.status.id, us2.status.id)

    data = {}
    response = client.get(url, data)
    assert len(response.data) == 2


def test_get_total_points(client):
    project = f.ProjectFactory.create()

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    points1 = f.PointsFactory.create(project=project, value=None)
    points2 = f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    us_with_points = f.UserStoryFactory.create(project=project)
    us_with_points.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_with_points, role=role1, points=points2)
    f.RolePointsFactory.create(user_story=us_with_points, role=role2, points=points3)

    assert us_with_points.get_total_points() == 3.0

    us_without_points = f.UserStoryFactory.create(project=project)
    us_without_points.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_without_points, role=role1, points=points1)
    f.RolePointsFactory.create(user_story=us_without_points, role=role2, points=points1)

    assert us_without_points.get_total_points() is None

    us_mixed = f.UserStoryFactory.create(project=project)
    us_mixed.role_points.all().delete()
    f.RolePointsFactory.create(user_story=us_mixed, role=role1, points=points1)
    f.RolePointsFactory.create(user_story=us_mixed, role=role2, points=points2)

    assert us_mixed.get_total_points() == 1.0


def test_api_filter_by_created_date(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = timezone.now() - timedelta(days=1)

    old_userstory = f.create_userstory(owner=user, created_date=one_day_ago)
    userstory = f.create_userstory(owner=user, subject="test")

    url = reverse("userstories-list") + "?created_date=%s" % (
        quote(userstory.created_date.isoformat())
    )

    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 1
    assert response.data[0]["subject"] == userstory.subject


def test_api_filter_by_created_date__lt(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = timezone.now() - timedelta(days=1)

    old_userstory = f.create_userstory(
        owner=user, created_date=one_day_ago, subject="old test"
    )
    userstory = f.create_userstory(owner=user)

    url = reverse("userstories-list") + "?created_date__lt=%s" % (
        quote(userstory.created_date.isoformat())
    )

    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert response.data[0]["subject"] == old_userstory.subject


def test_api_filter_by_created_date__lte(client):
    user = f.UserFactory(is_superuser=True)
    one_day_ago = timezone.now() - timedelta(days=1)

    old_userstory = f.create_userstory(owner=user, created_date=one_day_ago)
    userstory = f.create_userstory(owner=user)

    url = reverse("userstories-list") + "?created_date__lte=%s" % (
        quote(userstory.created_date.isoformat())
    )

    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 2


def test_api_filter_by_modified_date__gte(client):
    user = f.UserFactory(is_superuser=True)

    older_userstory = f.create_userstory(owner=user)
    userstory = f.create_userstory(owner=user, subject="test")
    # we have to refresh as it slightly differs
    userstory.refresh_from_db()

    assert older_userstory.modified_date < userstory.modified_date

    url = reverse("userstories-list") + "?modified_date__gte=%s" % (
        quote(userstory.modified_date.isoformat())
    )

    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 1
    assert response.data[0]["subject"] == userstory.subject


def test_api_filter_by_finish_date(client):
    user = f.UserFactory(is_superuser=True)
    one_day_later = timezone.now() + timedelta(days=1)

    userstory = f.create_userstory(owner=user)
    userstory_to_finish = f.create_userstory(
        owner=user, finish_date=one_day_later, subject="test"
    )

    assert userstory_to_finish.finish_date

    url = reverse("userstories-list") + "?finish_date__gte=%s" % (
        quote(userstory_to_finish.finish_date.isoformat())
    )
    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 1
    assert response.data[0]["subject"] == userstory_to_finish.subject


def test_api_filter_by_assigned_users(client):
    user = f.UserFactory(is_superuser=True)
    user2 = f.UserFactory(is_superuser=True)
    project = f.ProjectFactory.create(owner=user)

    f.MembershipFactory.create(user=user, project=project)

    f.create_userstory(owner=user, subject="test 2 users", assigned_to=user,
                       assigned_users=[user.id, user2.id], project=project)
    f.create_userstory(
        owner=user, subject="test 1 user", assigned_to=user,
        assigned_users=[user.id], project=project
    )

    url = reverse("userstories-list") + "?assigned_users=%s" % (user.id)

    client.login(user)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 2


def test_regresion_api_filter_by_assigned_users_for_no_members(client):
    user = f.UserFactory()
    user2 = f.UserFactory()
    user3 = f.UserFactory()
    project = f.create_project(is_private=False,
                               anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                               public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)) + ["comment_us"],
                               owner=user)

    f.MembershipFactory(project=project,
                        user=user,
                        role__project=project,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    f.MembershipFactory(project=project,
                        user=user2,
                        role__project=project,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    f.create_userstory(project=project, subject="test 1", assigned_to=user,
                       assigned_users=[user.id, user2.id])
    f.create_userstory(project=project, subject="test 2", assigned_to=user,
                       assigned_users=[user.id])
    f.create_userstory(project=project, subject="test 3")

    url = reverse("userstories-list") + "?assigned_users=%s" % (user.id)

    # Project owner
    client.login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data)  == 2

    # Member
    client.login(user2)
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data)  == 2

    # No member
    client.login(user3)
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data)  == 2

    # Anonymous user
    client.logout()
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data)  == 2


def test_api_filter_by_role(client):
    project = f.ProjectFactory.create()
    role1 = f.RoleFactory.create()

    user = f.UserFactory(is_superuser=True)
    user2 = f.UserFactory(is_superuser=True)
    f.MembershipFactory.create(user=user2, project=project, role=role1)

    userstory = f.create_userstory(owner=user, subject="test 2 users",
                                   assigned_to=user,
                                   assigned_users=[user.id, user2.id],
                                   project=project)
    f.create_userstory(
        owner=user, subject="test 1 user", assigned_to=user,
        assigned_users=[user.id],
        project=project
    )

    url = reverse("userstories-list") + "?role=%s" % (role1.id)

    client.login(userstory.owner)
    response = client.get(url)
    number_of_userstories = len(response.data)

    assert response.status_code == 200
    assert number_of_userstories == 1


@pytest.mark.parametrize("field_name", ["estimated_start", "estimated_finish"])
def test_api_filter_by_milestone__estimated_start_and_end(client, field_name):
    user = f.UserFactory(is_superuser=True)
    userstory = f.create_userstory(owner=user)

    assert userstory.milestone
    assert hasattr(userstory.milestone, field_name)
    date = getattr(userstory.milestone, field_name)
    before = (date - timedelta(days=1)).isoformat()
    after = (date + timedelta(days=1)).isoformat()

    client.login(userstory.owner)

    full_field_name = "milestone__" + field_name
    expections = {
        full_field_name + "__gte=" + quote(before): 1,
        full_field_name + "__gte=" + quote(after): 0,
        full_field_name + "__lte=" + quote(before): 0,
        full_field_name + "__lte=" + quote(after): 1
    }

    for param, expection in expections.items():
        url = reverse("userstories-list") + "?" + param
        response = client.get(url)
        number_of_userstories = len(response.data)

        assert response.status_code == 200
        assert number_of_userstories == expection, param
        if number_of_userstories > 0:
            assert response.data[0]["subject"] == userstory.subject


def test_api_filters_data(client):
    data = create_uss_fixtures()
    project = data["project"]
    (user1, user2, user3, ) = data["users"]
    (status0, status1, status2, status3, ) = data["statuses"]
    (epic0, epic1, epic2, ) = data["epics"]
    (tag0, tag1, tag2, tag3, ) = data["tags"]

    url = reverse("userstories-filters-data") + "?project={}".format(project.id)
    client.login(user1)

    # Check filter fields
    response = client.get(url)
    assert response.status_code == 200

    owners = next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))
    assert len(owners) == 6
    assert 'id' in owners
    assert 'count' in owners
    assert 'full_name' in owners
    assert 'photo' in owners
    assert 'big_photo' in owners
    assert 'gravatar_id' in owners

    assigned_users = next(filter(lambda i: i['id'] == user1.id, response.data["assigned_users"]))
    assert len(assigned_users) == 6
    assert 'id' in assigned_users
    assert 'count' in assigned_users
    assert 'full_name' in assigned_users
    assert 'photo' in assigned_users
    assert 'big_photo' in assigned_users
    assert 'gravatar_id' in assigned_users

    # No filter
    response = client.get(url)
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 4
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 3

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 4
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_users"]))["count"] == 5
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_users"]))["count"] == 2

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 4

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 1
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 5
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 4
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 4

    assert next(filter(lambda i: i['id'] is None, response.data["epics"]))["count"] == 5
    assert next(filter(lambda i: i['id'] == epic0.id, response.data["epics"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == epic1.id, response.data["epics"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == epic2.id, response.data["epics"]))["count"] == 2

    # Filter ((status0 or status3)
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

    assert next(filter(lambda i: i['id'] is None, response.data["epics"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == epic0.id, response.data["epics"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == epic1.id, response.data["epics"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == epic2.id, response.data["epics"]))["count"] == 2

    # Filter ((tag1 and tag2) and (user1 or user2))
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

    assert next(filter(lambda i: i['id'] is None, response.data["epics"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == epic0.id, response.data["epics"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == epic1.id, response.data["epics"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == epic2.id, response.data["epics"]))["count"] == 1

    # Filter (epic0 epic2)
    response = client.get(url + "&epic={},{}".format(epic0.id, epic2.id))
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 1

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 0

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 3

    assert next(filter(lambda i: i['name'] == tag0, response.data["tags"]))["count"] == 0
    assert next(filter(lambda i: i['name'] == tag1, response.data["tags"]))["count"] == 4
    assert next(filter(lambda i: i['name'] == tag2, response.data["tags"]))["count"] == 2
    assert next(filter(lambda i: i['name'] == tag3, response.data["tags"]))["count"] == 1

    assert next(filter(lambda i: i['id'] is None, response.data["epics"]))["count"] == 5
    assert next(filter(lambda i: i['id'] == epic0.id, response.data["epics"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == epic1.id, response.data["epics"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == epic2.id, response.data["epics"]))["count"] == 2



@pytest.mark.parametrize("filter_name,collection,expected,exclude_expected,is_text", [
    ('status', 'statuses', 3, 7, False),
    ('tags', 'tags', 1, 9, True),
    ('owner', 'users', 3, 7, False),
    ('role', 'roles', 5, 5, False),
    ('assigned_users', 'users', 5, 5, False),
])
def test_api_filters(client, filter_name, collection, expected, exclude_expected, is_text):
    data = create_uss_fixtures()
    project = data["project"]
    options = data[collection]

    client.login(data["users"][0])
    if is_text:
        param = options[0]
    else:
        param = options[0].id

    # include test
    url = "{}?project={}&&{}={}".format(reverse('userstories-list'), project.id, filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == expected
    assert "taiga-info-backlog-total-userstories" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Backlog-Total-Userstories") == False

    # exclude test
    url = "{}?project={}&&exclude_{}={}".format(reverse('userstories-list'), project.id,
                                               filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == exclude_expected
    assert "taiga-info-backlog-total-userstories" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Backlog-Total-Userstories") == False


@pytest.mark.parametrize("filter_name,collection,expected,exclude_expected,backlog_total_uss,is_text", [
    ('status', 'statuses', 1, 4, 5, False),
    ('tags', 'tags', 0, 5, 5, True),
    ('owner', 'users', 1, 4, 5, False),
    ('role', 'roles', 2, 3, 5, False),
    ('assigned_users', 'users', 2, 3, 5, False),
])
def test_api_filters_for_backlog(client, filter_name, collection, expected, exclude_expected, backlog_total_uss, is_text):
    data = create_uss_fixtures()
    project = data["project"]
    options = data[collection]

    client.login(data["users"][0])
    if is_text:
        param = options[0]
    else:
        param = options[0].id

    # include test
    url = "{}?project={}&milestone=null&{}={}".format(reverse('userstories-list'), project.id, filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == expected
    assert "taiga-info-backlog-total-userstories" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Backlog-Total-Userstories") == True
    assert response["taiga-info-backlog-total-userstories"] == f"{backlog_total_uss}"

    # exclude test
    url = "{}?project={}&milestone=null&exclude_{}={}".format(reverse('userstories-list'), project.id,
                                               filter_name, param)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == exclude_expected
    assert "taiga-info-backlog-total-userstories" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Backlog-Total-Userstories") == True
    assert response["taiga-info-backlog-total-userstories"] ==  f"{backlog_total_uss}"


def test_api_filters_tags_or_operator(client):
    data = create_uss_fixtures()
    project = data["project"]
    client.login(data["users"][0])
    tags = data["tags"]

    url = "{}?project={}&tags={},{}".format(reverse('userstories-list'), project.id, tags[0],
                                            tags[2])
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 5


def test_api_filters_data_with_assigned_users(client):
    project = f.ProjectFactory.create()
    user1 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user1, project=project)
    user2 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user2, project=project)
    user3 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user3, project=project)

    status0 = f.UserStoryStatusFactory.create(project=project)
    status1 = f.UserStoryStatusFactory.create(project=project)
    status2 = f.UserStoryStatusFactory.create(project=project)
    status3 = f.UserStoryStatusFactory.create(project=project)

    # -----------------------------------------------------------
    # | US    | Status  |  Owner | Assigned To | Assigned Users |
    # |-------#---------#--------#-------------#-----------------
    # | 0     | status3 |  user2 | user2       | user2, user3   |
    # | 1     | status3 |  user1 | None        | None           |
    # | 2     | status1 |  user3 | None        | None           |
    # | 3     | status0 |  user2 | None        | None           |
    # | 4     | status0 |  user1 | user1       | user1          |
    # -----------------------------------------------------------

    us0 = f.UserStoryFactory.create(project=project, owner=user2,
                                    assigned_to=user2,
                                    assigned_users=[user2, user3],
                                    status=status3)
    f.RelatedUserStory.create(user_story=us0)
    us1 = f.UserStoryFactory.create(project=project, owner=user1,
                                    assigned_to=None,
                                    status=status3, )
    us2 = f.UserStoryFactory.create(project=project, owner=user3,
                                    assigned_to=None,
                                    status=status1)
    f.RelatedUserStory.create(user_story=us2)
    us3 = f.UserStoryFactory.create(project=project, owner=user2,
                                    assigned_to=None,
                                    status=status0)
    us4 = f.UserStoryFactory.create(project=project, owner=user1,
                                    assigned_to=user1,
                                    assigned_users=[user1],
                                    status=status0)

    url = reverse("userstories-filters-data") + "?project={}".format(project.id)

    client.login(user1)

    # Check filter fields
    response = client.get(url)
    assert response.status_code == 200

    owners = next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))
    assert len(owners) == 6
    assert 'id' in owners
    assert 'count' in owners
    assert 'full_name' in owners
    assert 'photo' in owners
    assert 'big_photo' in owners
    assert 'gravatar_id' in owners

    assigned_users = next(filter(lambda i: i['id'] == user1.id, response.data["assigned_users"]))
    assert len(assigned_users) == 6
    assert 'id' in assigned_users
    assert 'count' in assigned_users
    assert 'full_name' in assigned_users
    assert 'photo' in assigned_users
    assert 'big_photo' in assigned_users
    assert 'gravatar_id' in assigned_users

    # No filter
    response = client.get(url)
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user3.id, response.data["owners"]))["count"] == 1

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 3
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user3.id, response.data["assigned_to"]))["count"] == 0

    assert next(filter(lambda i: i['id'] == status0.id, response.data["statuses"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == status1.id, response.data["statuses"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == status2.id, response.data["statuses"]))["count"] == 0
    assert next(filter(lambda i: i['id'] == status3.id, response.data["statuses"]))["count"] == 2

    assert next(filter(lambda i: i['id'] == user1.id,
                       response.data["assigned_users"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id,
                       response.data["assigned_users"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user3.id,
                       response.data["assigned_users"]))["count"] == 1


def test_api_filters_data_roles_with_assigned_users(client):
    project = f.ProjectFactory.create()

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    user1 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user1, project=project, role=role1)
    user2 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user2, project=project, role=role2)
    user3 = f.UserFactory.create(is_superuser=True)
    f.MembershipFactory.create(user=user3, project=project, role=role1)


    # ----------------------------------------------------------------
    # | US    |  Owner | Assigned To | Assigned Users | Role         |
    # |-------#--------#-------------#----------------#---------------
    # | 0     |  user2 | user2       | user2, user3   | role2, role1 |
    # | 1     |  user1 | None        | None           | None         |
    # | 2     |  user1 | user1       | user1          | role1        |
    # ----------------------------------------------------------------

    us0 = f.UserStoryFactory.create(project=project, owner=user2, status__project=project,
                                    assigned_to=user2,
                                    assigned_users=[user2, user3],)
    f.RelatedUserStory.create(user_story=us0)
    us1 = f.UserStoryFactory.create(project=project, owner=user1, status__project=project,
                                    assigned_to=None)
    us2 = f.UserStoryFactory.create(project=project, owner=user1, status__project=project,
                                    assigned_to=user1,
                                    assigned_users=[user1],)

    url = reverse("userstories-filters-data") + "?project={}".format(project.id)

    client.login(user1)

    # No filter
    response = client.get(url)
    assert response.status_code == 200

    assert next(filter(lambda i: i['id'] == user1.id, response.data["owners"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == user2.id, response.data["owners"]))["count"] == 1

    assert next(filter(lambda i: i['id'] is None, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user1.id, response.data["assigned_to"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id, response.data["assigned_to"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == user1.id,
                       response.data["assigned_users"]))["count"] == 1
    assert next(filter(lambda i: i['id'] == user2.id,
                       response.data["assigned_users"]))["count"] == 1

    assert next(filter(lambda i: i['id'] == role1.id,
                       response.data["roles"]))["count"] == 2
    assert next(filter(lambda i: i['id'] == role2.id,
                       response.data["roles"]))["count"] == 1


def test_get_invalid_csv(client):
    url = reverse("userstories-csv")
    project = f.ProjectFactory.create()

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 404

    response = client.get("{}?uuid={}".format(url, "not-valid-uuid"))
    assert response.status_code == 404


def test_get_valid_csv(client):
    url = reverse("userstories-csv")
    project = f.ProjectFactory.create(userstories_csv_uuid=uuid.uuid4().hex)

    response = client.get(
        "{}?uuid={}".format(url, project.userstories_csv_uuid))
    assert response.status_code == 200


def test_custom_fields_csv_generation():
    project = f.ProjectFactory.create(userstories_csv_uuid=uuid.uuid4().hex)
    attr = f.UserStoryCustomAttributeFactory.create(project=project,
                                                    name="attr1",
                                                    description="desc")
    us = f.UserStoryFactory.create(project=project)
    attr_values = us.custom_attributes_values
    attr_values.attributes_values = {str(attr.id): "val1"}
    attr_values.save()
    queryset = project.user_stories.all()
    data = services.userstories_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)

    assert row.pop() == attr.name
    row = next(reader)
    assert row.pop() == "val1"


def test_update_userstory_respecting_watchers(client):
    watching_user = f.create_user()
    project = f.ProjectFactory.create()
    us = f.UserStoryFactory.create(project=project, status__project=project,
                                   milestone__project=project)
    us.add_watcher(watching_user)
    f.MembershipFactory.create(project=us.project, user=us.owner,
                               is_admin=True)
    f.MembershipFactory.create(project=us.project, user=watching_user)

    client.login(user=us.owner)
    url = reverse("userstories-detail", kwargs={"pk": us.pk})
    data = {"subject": "Updating test", "version": 1}

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["subject"] == "Updating test"
    assert response.data["watchers"] == [watching_user.id]


def test_update_userstory_update_watchers(client):
    watching_user = f.create_user()
    project = f.ProjectFactory.create()
    us = f.UserStoryFactory.create(project=project, status__project=project,
                                   milestone__project=project)
    f.MembershipFactory.create(project=us.project, user=us.owner,
                               is_admin=True)
    f.MembershipFactory.create(project=us.project, user=watching_user)

    client.login(user=us.owner)
    url = reverse("userstories-detail", kwargs={"pk": us.pk})
    data = {"watchers": [watching_user.id], "version": 1}

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["watchers"] == [watching_user.id]
    watcher_ids = list(us.get_watchers().values_list("id", flat=True))
    assert watcher_ids == [watching_user.id]


def test_update_userstory_remove_watchers(client):
    watching_user = f.create_user()
    project = f.ProjectFactory.create()
    us = f.UserStoryFactory.create(project=project, status__project=project,
                                   milestone__project=project)
    us.add_watcher(watching_user)
    f.MembershipFactory.create(project=us.project, user=us.owner,
                               is_admin=True)
    f.MembershipFactory.create(project=us.project, user=watching_user)

    client.login(user=us.owner)
    url = reverse("userstories-detail", kwargs={"pk": us.pk})
    data = {"watchers": [], "version": 1}

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["watchers"] == []
    watcher_ids = list(us.get_watchers().values_list("id", flat=True))
    assert watcher_ids == []


def test_update_userstory_update_tribe_gig(client):
    project = f.ProjectFactory.create()
    us = f.UserStoryFactory.create(project=project, status__project=project,
                                   milestone__project=project)
    f.MembershipFactory.create(project=us.project, user=us.owner,
                               is_admin=True)

    url = reverse("userstories-detail", kwargs={"pk": us.pk})
    data = {
        "tribe_gig": {
            "id": 2,
            "title": "This is a gig test title"
        },
        "version": 1
    }

    client.login(user=us.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200
    assert response.data["tribe_gig"] == data["tribe_gig"]


def test_get_user_stories_including_tasks(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    user_story = f.UserStoryFactory.create(project=project)
    f.TaskFactory.create(user_story=user_story)
    url = reverse("userstories-list")

    client.login(project.owner)

    response = client.get(url)
    assert response.status_code == 200
    assert response.data[0].get("tasks") == []

    url = reverse("userstories-list") + "?include_tasks=1"
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data[0].get("tasks")) == 1


def test_get_user_stories_including_attachments(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    user_story = f.UserStoryFactory.create(project=project)
    f.UserStoryAttachmentFactory(project=project, content_object=user_story)
    url = reverse("userstories-list")

    client.login(project.owner)

    response = client.get(url)
    assert response.status_code == 200
    assert response.data[0].get("attachments") == []

    url = reverse("userstories-list") + "?include_attachments=1"
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data[0].get("attachments")) == 1


def test_api_validator_assigned_to_when_update_userstories(client):
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
    userstory = f.create_userstory(project=project, owner=project.owner, status=project.us_statuses.all()[0])

    url = reverse('userstories-detail', kwargs={"pk": userstory.pk})

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


def test_api_validator_assigned_to_when_create_userstories(client):
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

    url = reverse('userstories-list')

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


def test_update_userstory_backlog_order(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project, owner=user1, status__project=project, milestone=None, backlog_order=0)
    us2 = f.create_userstory(project=project, owner=user1, status__project=project, milestone=None, backlog_order=1)
    us3 = f.create_userstory(project=project, owner=user1, status__project=project, milestone=None, backlog_order=2)
    us4 = f.create_userstory(project=project, owner=user1, status__project=project, milestone=None, backlog_order=3)
    url = reverse("userstories-detail", args=[us4.pk])

    data = {
        "version": us1.version,
        "backlog_order": 1
    }

    client.login(project.owner)

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data
    assert 1 == response.data['backlog_order']

    url = reverse("userstories-list") + "?milestone=null&project={}".format(project.id)
    client.login(project.owner)
    response = client.get(url)
    user_stories = response.data
    number_of_stories = len(user_stories)

    assert response.status_code == 200
    assert number_of_stories == 4, number_of_stories
    assert 0 == user_stories[0]["backlog_order"]
    assert us1.id == user_stories[0]["id"]
    assert us4.id == user_stories[1]["id"]
    assert 1 == user_stories[1]["backlog_order"]
    assert us2.id == user_stories[2]["id"]
    assert 2 == user_stories[2]["backlog_order"]
    assert us3.id == user_stories[3]["id"]
    assert 3 == user_stories[3]["backlog_order"]



def test_api_update_change_kanban_order_if_project_change(client):
    user1 = f.UserFactory.create()
    project1 = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project1, user=project1.owner, is_admin=True)
    project2 = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project2, user=project2.owner, is_admin=True)
    us = f.create_userstory(project=project1, owner=user1, status=project1.default_us_status)

    url = reverse("userstories-detail", args=[us.pk])
    data = {
        "version": us.version,
        "project": project2.id,
        "status": project2.default_us_status.id,
        "milestone": None,
    }

    client.login(project1.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    assert us.kanban_order < response.data["kanban_order"]
    assert project2.id == response.data["project"]


def test_api_update_change_kanban_order_if_status_change(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    status1 = f.UserStoryStatusFactory(project=project)
    status2 = f.UserStoryStatusFactory(project=project)
    us = f.create_userstory(project=project, owner=user1,
            status=status1, swimlane=project.default_swimlane)

    url = reverse("userstories-detail", args=[us.pk])
    data = {
        "version": us.version,
        "status": status2.id
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    assert us.kanban_order < response.data["kanban_order"]
    assert status2.id == response.data["status"]


def test_api_update_change_kanban_order_if_swimlane_change(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    swimlane1 = f.SwimlaneFactory(project=project)
    swimlane2 = f.SwimlaneFactory(project=project)
    us = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)

    url = reverse("userstories-detail", args=[us.pk])
    data = {
        "version": us.version,
        "swimlane": swimlane2.id
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    assert us.kanban_order < response.data["kanban_order"]
    assert swimlane2.id == response.data["swimlane"]


def test_api_headers_userstories_without_swimlane_false(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    swimlane1 = f.SwimlaneFactory(project=project)
    us1 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)
    us3 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)

    url = f"{reverse('userstories-list')}?project={project.id}"

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert "taiga-info-userstories-without-swimlane" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Userstories-Without-Swimlane") == True
    assert response["taiga-info-userstories-without-swimlane"] == "false"


def test_api_headers_userstories_without_swimlane_true(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    swimlane1 = f.SwimlaneFactory(project=project)
    us1 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=None)
    us3 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)

    url = f"{reverse('userstories-list')}?project={project.id}"

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert "taiga-info-userstories-without-swimlane" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Userstories-Without-Swimlane") == True
    assert response["taiga-info-userstories-without-swimlane"] == "true"


def test_api_headers_userstories_without_swimlane_not_send(client):
    user1 = f.UserFactory.create()
    project = f.create_project(owner=user1)
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    swimlane1 = f.SwimlaneFactory(project=project)
    us1 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)
    us2 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=None)
    us3 = f.create_userstory(project=project, owner=user1,
            status=project.default_us_status, swimlane=swimlane1)

    url = reverse('userstories-list')

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert "taiga-info-userstories-without-swimlane" in response["access-control-expose-headers"]
    assert response.has_header("Taiga-Info-Userstories-Without-Swimlane") == False


def test_api_list_userstory_using_onlyref_serializer(client):
    project = f.create_project(owner=f.UserFactory.create())
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)
    us3 = f.create_userstory(project=project)

    url = f"{reverse('userstories-list')}?only_ref=true"

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert set(response.data[0].keys()) == set(["id", "ref"])


def test_bug_regresion_api_by_ref_userstory_using_onlyref_serializer(client):
    # Prevent error triying to get detail of userstory with only_ref=true
    #
    #   File ".../taiga-back/taiga/projects/userstories/serializers.py", line 124, in get_points
    #       assert hasattr(obj, "role_points_attr"), "instance must have a role_points_attr attribute"
    #   AssertionError: instance must have a role_points_attr attribute

    project = f.create_project(owner=f.UserFactory.create())
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us1 = f.create_userstory(project=project)

    url = f"{reverse('userstories-by-ref')}?include_attachments=true&include_tasks=true&only_ref=true&page=40&project={us1.project_id}&ref={us1.ref}"

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert set(response.data.keys()) != set(["id", "ref"])

    url = f"{reverse('userstories-detail', args=[us1.id])}?include_attachments=true&include_tasks=true&only_ref=true"

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 200, response.data
    assert set(response.data.keys()) != set(["id", "ref"])
