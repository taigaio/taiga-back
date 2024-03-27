# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.urls import reverse
from django.conf import settings
from django.core.files import File
from django.core import mail
from django.core import signing

from taiga.base import exceptions as exc
from taiga.base.utils import json
from taiga.projects.services import stats as stats_services
from taiga.projects.history.services import take_snapshot
from taiga.permissions.choices import ANON_PERMISSIONS
from taiga.projects.models import Project, Swimlane
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.epics.models import Epic
from taiga.projects.choices import BLOCKED_BY_DELETING
from taiga.timeline.service import get_project_timeline

from .. import factories as f
from ..utils import DUMMY_BMP_DATA

from tempfile import NamedTemporaryFile
from easy_thumbnails.files import generate_all_aliases, get_thumbnailer

import os.path
import pytest

from unittest import mock


pytestmark = pytest.mark.django_db


class ExpiredSigner(signing.TimestampSigner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.salt = "django.core.signing.TimestampSigner"

    def timestamp(self):
        from django.utils import baseconv
        import time
        time_in_the_far_past = int(time.time()) - 24*60*60*1000
        return baseconv.base62.encode(time_in_the_far_past)


def test_get_project_detail(client):
    # api/v1/projects/2
    project = f.create_project(is_private=False,
                               anon_permissions=['view_project'],
                               public_permissions=['view_project'])
    url = reverse("projects-detail", kwargs={"pk": project.id})

    # anonymous access but public project
    response = client.json.get(url)
    assert response.status_code == 200


def test_get_wrong_project_detail_using_slug_instead_pk(client):
    # api/v1/projects/project-2 (bad pk)
    project = f.create_project(is_private=True)
    url = reverse("projects-detail", kwargs={"pk": project.slug})

    response = client.json.get(url)
    assert response.status_code == 401

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 404


def test_get_private_project_by_slug(client):
    # api/v1/projects/by_slug?slug=project-2
    project = f.create_project(is_private=True)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)

    url = reverse("projects-by-slug")

    response = client.json.get(url, {"slug": project.slug})

    assert response.status_code == 401

    client.login(project.owner)
    response = client.json.get(url, {"slug": project.slug})
    assert response.status_code == 200


def test_create_project(client):
    user = f.create_user()
    url = reverse("projects-list")
    data = {"name": "project name", "description": "project description"}

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_create_private_project_without_enough_private_projects_slots(client):
    user = f.create_user(max_private_projects=0)
    url = reverse("projects-list")
    data = {
        "name": "project name",
        "description": "project description",
        "is_private": True
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more private projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "True"


def test_create_public_project_without_enough_public_projects_slots(client):
    user = f.create_user(max_public_projects=0)
    url = reverse("projects-list")
    data = {
        "name": "project name",
        "description": "project description",
        "is_private": False
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more public projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_change_project_from_private_to_public_without_enough_public_projects_slots(client):
    project = f.create_project(is_private=True, owner__max_public_projects=0)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    data = {
        "is_private": False
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more public projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_change_project_from_public_to_private_without_enough_private_projects_slots(client):
    project = f.create_project(is_private=False, owner__max_private_projects=0)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    data = {
        "is_private": True
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more private projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "True"


def test_create_private_project_with_enough_private_projects_slots(client):
    user = f.create_user(max_private_projects=1)
    url = reverse("projects-list")
    data = {
        "name": "project name",
        "description": "project description",
        "is_private": True
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_create_public_project_with_enough_public_projects_slots(client):
    user = f.create_user(max_public_projects=1)
    url = reverse("projects-list")
    data = {
        "name": "project name",
        "description": "project description",
        "is_private": False
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_change_project_from_private_to_public_with_enough_public_projects_slots(client):
    project = f.create_project(is_private=True, owner__max_public_projects=1)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    data = {
        "is_private": False
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200


def test_change_project_from_public_to_private_with_enough_private_projects_slots(client):
    project = f.create_project(is_private=False, owner__max_private_projects=1)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    data = {
        "is_private": True
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200


def test_change_project_other_data_with_enough_private_projects_slots(client):
    project = f.create_project(is_private=True, owner__max_private_projects=1)
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})

    data = {
        "name": "test-project-change"
    }

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200


def test_partially_update_project(client):
    project = f.create_project()
    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse("projects-detail", kwargs={"pk": project.pk})
    data = {"name": ""}

    client.login(project.owner)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_us_status_is_closed_changed_recalc_us_is_closed(client):
    us_status = f.UserStoryStatusFactory(is_closed=False)
    user_story = f.UserStoryFactory.create(project=us_status.project, status=us_status)

    assert user_story.is_closed is False

    us_status.is_closed = True
    us_status.save()

    user_story.refresh_from_db()
    assert user_story.is_closed is True

    us_status.is_closed = False
    us_status.save()

    user_story.refresh_from_db()
    assert user_story.is_closed is False


def test_task_status_is_closed_changed_recalc_us_is_closed(client):
    us_status = f.UserStoryStatusFactory()
    user_story = f.UserStoryFactory.create(project=us_status.project, status=us_status)
    task_status = f.TaskStatusFactory.create(project=us_status.project, is_closed=False)
    f.TaskFactory.create(project=us_status.project, status=task_status, user_story=user_story)

    assert user_story.is_closed is False

    task_status.is_closed = True
    task_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is True

    task_status.is_closed = False
    task_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is False


def test_us_status_slug_generation(client):
    us_status = f.UserStoryStatusFactory(name="NEW")
    f.MembershipFactory(user=us_status.project.owner, project=us_status.project, is_admin=True)
    assert us_status.slug == "new"

    client.login(us_status.project.owner)

    url = reverse("userstory-statuses-detail", kwargs={"pk": us_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_task_status_slug_generation(client):
    task_status = f.TaskStatusFactory(name="NEW")
    f.MembershipFactory(user=task_status.project.owner, project=task_status.project, is_admin=True)
    assert task_status.slug == "new"

    client.login(task_status.project.owner)

    url = reverse("task-statuses-detail", kwargs={"pk": task_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_issue_status_slug_generation(client):
    issue_status = f.IssueStatusFactory(name="NEW")
    f.MembershipFactory(user=issue_status.project.owner, project=issue_status.project, is_admin=True)
    assert issue_status.slug == "new"

    client.login(issue_status.project.owner)

    url = reverse("issue-statuses-detail", kwargs={"pk": issue_status.pk})

    data = {"name": "new"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new"

    data = {"name": "new status"}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["slug"] == "new-status"


def test_points_name_duplicated(client):
    point_1 = f.PointsFactory()
    point_2 = f.PointsFactory(project=point_1.project)
    f.MembershipFactory(user=point_1.project.owner, project=point_1.project, is_admin=True)
    client.login(point_1.project.owner)

    url = reverse("points-detail", kwargs={"pk": point_2.pk})
    data = {"name": point_1.name}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400
    assert response.data["name"][0] == "Duplicated name"


def test_update_points_when_not_null_values_for_points(client):
    points = f.PointsFactory(name="?", value="6")
    f.RoleFactory(project=points.project, computable=True)
    assert points.project.points.filter(value__isnull=True).count() == 0
    points.project.update_role_points()
    assert points.project.points.filter(value__isnull=True).count() == 1


def test_get_closed_bugs_per_member_stats():
    project = f.ProjectFactory()
    membership_1 = f.MembershipFactory(project=project)
    membership_2 = f.MembershipFactory(project=project)
    issue_closed_status = f.IssueStatusFactory(is_closed=True, project=project)
    issue_open_status = f.IssueStatusFactory(is_closed=False, project=project)
    f.IssueFactory(project=project,
                   status=issue_closed_status,
                   owner=membership_1.user,
                   assigned_to=membership_1.user)
    f.IssueFactory(project=project,
                   status=issue_open_status,
                   owner=membership_2.user,
                   assigned_to=membership_2.user)
    task_closed_status = f.TaskStatusFactory(is_closed=True, project=project)
    task_open_status = f.TaskStatusFactory(is_closed=False, project=project)
    f.TaskFactory(project=project,
                  status=task_closed_status,
                  owner=membership_1.user,
                  assigned_to=membership_1.user)
    f.TaskFactory(project=project,
                  status=task_open_status,
                  owner=membership_2.user,
                  assigned_to=membership_2.user)
    f.TaskFactory(project=project,
                  status=task_open_status,
                  owner=membership_2.user,
                  assigned_to=membership_2.user,
                  is_iocaine=True)

    wiki_page = f.WikiPageFactory.create(project=project, owner=membership_1.user)
    take_snapshot(wiki_page, user=membership_1.user)
    wiki_page.content = "Frontend, future"
    wiki_page.save()
    take_snapshot(wiki_page, user=membership_1.user)

    stats = stats_services.get_member_stats_for_project(project)

    assert stats["closed_bugs"][membership_1.user.id] == 1
    assert stats["closed_bugs"][membership_2.user.id] == 0

    assert stats["iocaine_tasks"][membership_1.user.id] == 0
    assert stats["iocaine_tasks"][membership_2.user.id] == 1

    assert stats["wiki_changes"][membership_1.user.id] == 2
    assert stats["wiki_changes"][membership_2.user.id] == 0

    assert stats["created_bugs"][membership_1.user.id] == 1
    assert stats["created_bugs"][membership_2.user.id] == 1

    assert stats["closed_tasks"][membership_1.user.id] == 1
    assert stats["closed_tasks"][membership_2.user.id] == 0


def test_leave_project_valid_membership(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 200


def test_leave_project_valid_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 403
    assert response.data["_error_message"] == "You can't leave the project if you are the owner or there are no more admins"


def test_leave_project_valid_membership_real_owner(client):
    owner_user = f.UserFactory.create()
    member_user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=owner_user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=owner_user, role=role, is_admin=True)
    f.MembershipFactory.create(project=project, user=member_user, role=role, is_admin=True)

    client.login(owner_user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 403
    assert response.data["_error_message"] == "You can't leave the project if you are the owner or there are no more admins"


def test_leave_project_invalid_membership(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory()
    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 404


def test_leave_project_respect_watching_items(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role)
    issue = f.IssueFactory(owner=user)
    issue.watchers=[user]
    issue.save()

    client.login(user)
    url = reverse("projects-leave", args=(project.id,))
    response = client.post(url)
    assert response.status_code == 200
    assert issue.watchers == [user]


def test_delete_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    client.login(user)
    url = reverse("memberships-detail", args=(membership.id,))
    response = client.delete(url)
    assert response.status_code == 400
    assert response.data["_error_message"] == "The project must have an owner and at least one of the users must be an active admin"


def test_delete_membership_real_owner(client):
    owner_user = f.UserFactory.create()
    member_user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=owner_user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    owner_membership = f.MembershipFactory.create(project=project, user=owner_user, role=role, is_admin=True)
    f.MembershipFactory.create(project=project, user=member_user, role=role, is_admin=True)

    client.login(owner_user)
    url = reverse("memberships-detail", args=(owner_membership.id,))
    response = client.delete(url)
    assert response.status_code == 400
    assert response.data["_error_message"] == "The project must have an owner and at least one of the users must be an active admin"


def test_edit_membership_only_owner(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create()
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    data = {
        "is_admin": False
    }
    client.login(user)
    url = reverse("memberships-detail", args=(membership.id,))
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400
    assert response.data["is_admin"][0] == "At least one user must be an active admin for this project."


def test_anon_permissions_generation_when_making_project_public(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(is_private=True)
    role = f.RoleFactory.create(project=project, permissions=["view_project", "modify_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    assert project.anon_permissions == []
    client.login(user)
    url = reverse("projects-detail", kwargs={"pk": project.pk})
    data = {"is_private": False}
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
    assert set(anon_permissions).issubset(set(response.data["anon_permissions"]))
    assert set(anon_permissions).issubset(set(response.data["public_permissions"]))


def test_destroy_point_and_reassign(client):
    project = f.ProjectFactory.create()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    p1 = f.PointsFactory(project=project)
    project.default_points = p1
    project.save()
    p2 = f.PointsFactory(project=project)
    user_story =  f.UserStoryFactory.create(project=project)
    rp1 = f.RolePointsFactory.create(user_story=user_story, points=p1)

    url = reverse("points-detail", args=[p1.pk]) + "?moveTo={}".format(p2.pk)

    client.login(project.owner)

    assert user_story.role_points.all()[0].points.id == p1.id
    assert project.default_points.id == p1.id

    response = client.delete(url)

    assert user_story.role_points.all()[0].points.id == p2.id
    project.refresh_from_db()
    assert project.default_points.id == p2.id


@pytest.mark.django_db(transaction=True)
def test_update_projects_order_in_bulk(client):
    user = f.create_user()
    client.login(user)
    membership_1 = f.MembershipFactory(user=user)
    membership_2 = f.MembershipFactory(user=user)

    url = reverse("projects-bulk-update-order")
    data = [
        {"project_id": membership_1.project.id, "order":100},
        {"project_id": membership_2.project.id, "order":200}
    ]

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 204
    assert user.memberships.get(project=membership_1.project).user_order == 100
    assert user.memberships.get(project=membership_2.project).user_order == 200


def test_create_and_use_template(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    role = f.RoleFactory(project=project)
    f.MembershipFactory(user=user, project=project, is_admin=True, role=role)
    client.login(user)

    url = reverse("projects-create-template", kwargs={"pk": project.pk})
    data = {
        "template_name": "test template",
        "template_description": "test template description"
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201

    template_id = response.data["id"]
    url = reverse("projects-list")
    data = {
        "name": "test project based on template",
        "description": "test project based on template",
        "creation_template": template_id,
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201


def test_projects_user_order(client):
    user = f.UserFactory.create(is_superuser=True)
    project_1 = f.create_project()
    role_1 = f.RoleFactory(project=project_1)
    f.MembershipFactory(user=user, project=project_1, is_admin=True, role=role_1, user_order=2)

    project_2 = f.create_project()
    role_2 = f.RoleFactory(project=project_2)
    f.MembershipFactory(user=user, project=project_2, is_admin=True, role=role_2, user_order=1)

    client.login(user)
    #Testing default id order
    url = reverse("projects-list")
    url = "%s?member=%s" % (url, user.id)
    response = client.json.get(url)
    response_content = response.data
    assert response.status_code == 200
    assert(response_content[0]["id"] == project_1.id)

    #Testing user order
    url = reverse("projects-list")
    url = "%s?member=%s&order_by=user_order" % (url, user.id)
    response = client.json.get(url)
    response_content = response.data
    assert response.status_code == 200
    assert(response_content[0]["id"] == project_2.id)


@pytest.mark.django_db(transaction=True)
def test_update_project_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-change-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)

        client.login(user)
        post_data = {'logo': logo}
        response = client.post(url, post_data)
        assert response.status_code == 200
        assert not any(list(map(os.path.exists, original_photo_paths)))


@pytest.mark.django_db(transaction=True)
def test_update_project_logo_with_long_file_name(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-change-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.name=500*"x"+".bmp"
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)

        client.login(user)
        post_data = {'logo': logo}
        response = client.post(url, post_data)

        assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_remove_project_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-remove-logo", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))
    client.login(user)
    response = client.post(url)
    assert response.status_code == 200
    assert not any(list(map(os.path.exists, original_photo_paths)))

@pytest.mark.django_db(transaction=True)
def test_remove_project_with_logo(client):
    user = f.UserFactory.create(is_superuser=True)
    project = f.create_project()
    url = reverse("projects-detail", args=(project.id,))

    with NamedTemporaryFile(delete=False) as logo:
        logo.write(DUMMY_BMP_DATA)
        logo.seek(0)
        project.logo = File(logo)
        project.save()
        generate_all_aliases(project.logo, include_global=True)

    thumbnailer = get_thumbnailer(project.logo)
    original_photo_paths = [project.logo.path]
    original_photo_paths += [th.path for th in thumbnailer.get_thumbnails()]

    assert all(list(map(os.path.exists, original_photo_paths)))
    client.login(user)
    response = client.delete(url)
    assert response.status_code == 204
    assert not any(list(map(os.path.exists, original_photo_paths)))


def test_project_list_without_search_query_order_by_name(client):
    user = f.UserFactory.create(is_superuser=True)
    project3 = f.create_project(name="test 3 - word", description="description 3", tags=["tag3"])
    project1 = f.create_project(name="test 1", description="description 1 - word", tags=["tag1"])
    project2 = f.create_project(name="test 2", description="description 2", tags=["word", "tag2"])

    url = reverse("projects-list")

    client.login(user)
    response = client.json.get(url)

    assert response.status_code == 200
    assert response.data[0]["id"] == project1.id
    assert response.data[1]["id"] == project2.id
    assert response.data[2]["id"] == project3.id


def test_project_list_with_search_query_order_by_ranking(client):
    user = f.UserFactory.create(is_superuser=True)
    project3 = f.create_project(name="test 3 - word", description="description 3", tags=["tag3"])
    project1 = f.create_project(name="test 1", description="description 1 - word", tags=["tag1"])
    project2 = f.create_project(name="test 2", description="description 2", tags=["word", "tag2"])
    project4 = f.create_project(name="test 4", description="description 4", tags=["tag4"])
    project5 = f.create_project(name="test 5", description="description 5", tags=["tag5"])

    url = reverse("projects-list")

    client.login(user)
    response = client.json.get(url, {"q": "word"})

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]["id"] == project3.id
    assert response.data[1]["id"] == project2.id
    assert response.data[2]["id"] == project1.id


####################################################################################
# Test transfer project ownership
####################################################################################


def test_transfer_request_from_not_anonimous(client):
    user = f.UserFactory.create()
    project = f.create_project(anon_permissions=["view_project"])

    url = reverse("projects-transfer-request", args=(project.id,))

    mail.outbox = []

    response = client.json.post(url)
    assert response.status_code == 401
    assert len(mail.outbox) == 0


def test_transfer_request_from_not_project_member(client):
    user = f.UserFactory.create()
    project = f.create_project(public_permissions=["view_project"])

    url = reverse("projects-transfer-request", args=(project.id,))

    mail.outbox = []

    client.login(user)
    response = client.json.post(url)
    assert response.status_code == 403
    assert len(mail.outbox) == 0


def test_transfer_request_from_not_admin_member(client):
    user = f.UserFactory.create()
    project = f.create_project()
    role = f.RoleFactory(project=project, permissions=["view_project"])
    f.create_membership(user=user, project=project, role=role, is_admin=False)

    url = reverse("projects-transfer-request", args=(project.id,))

    mail.outbox = []

    client.login(user)
    response = client.json.post(url)
    assert response.status_code == 403
    assert len(mail.outbox) == 0


def test_transfer_request_from_admin_member(client):
    user = f.UserFactory.create()
    project = f.create_project()
    role = f.RoleFactory(project=project, permissions=["view_project"])
    f.create_membership(user=user, project=project, role=role, is_admin=True)

    url = reverse("projects-transfer-request", args=(project.id,))

    mail.outbox = []

    client.login(user)
    response = client.json.post(url)
    assert response.status_code == 200
    assert len(mail.outbox) == 1


def test_project_transfer_start_to_not_a_membership(client):
    user_from = f.UserFactory.create()
    project = f.create_project(owner=user_from)
    f.create_membership(user=user_from, project=project, is_admin=True)

    client.login(user_from)
    url = reverse("projects-transfer-start", kwargs={"pk": project.pk})

    data = {
        "user": 666,
    }
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "The user doesn't exist" in response.data


def test_project_transfer_start_to_a_not_admin_member(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()
    project = f.create_project(owner=user_from)
    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_from)
    url = reverse("projects-transfer-start", kwargs={"pk": project.pk})

    data = {
        "user": user_to.id,
    }
    mail.outbox = []

    assert project.transfer_token is None
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.id)
    assert project.transfer_token is not None
    assert len(mail.outbox) == 1


def test_project_transfer_start_to_an_admin_member(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()
    project = f.create_project(owner=user_from)
    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=True)

    client.login(user_from)
    url = reverse("projects-transfer-start", kwargs={"pk": project.pk})

    data = {
        "user": user_to.id,
    }
    mail.outbox = []

    assert project.transfer_token is None
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.id)
    assert project.transfer_token is not None
    assert len(mail.outbox) == 1


def test_project_transfer_reject_from_member_without_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {}
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert len(mail.outbox) == 0


def test_project_transfer_reject_from_member_with_invalid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    project = f.create_project(owner=user_from, transfer_token="invalid-token")

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {
        "token": "invalid-token",
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_reject_from_member_with_other_user_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()
    other_user = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(other_user.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_reject_from_member_with_expired_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = ExpiredSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token has expired" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_reject_from_admin_member_with_valid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=True)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user_from.email]
    project = Project.objects.get(pk=project.pk)
    assert project.owner.id == user_from.id
    assert project.transfer_token is None


def test_project_transfer_reject_from_no_admin_member_with_valid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    m = f.create_membership(user=user_to, project=project, is_admin=False)

    client.login(user_to)
    url = reverse("projects-transfer-reject", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user_from.email]
    assert m.is_admin == False
    project = Project.objects.get(pk=project.pk)
    m = project.memberships.get(user=user_to)
    assert project.owner.id == user_from.id
    assert project.transfer_token is None
    assert m.is_admin == False


def test_project_transfer_accept_from_member_without_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {}
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert len(mail.outbox) == 0


def test_project_transfer_accept_from_member_with_invalid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    project = f.create_project(owner=user_from, transfer_token="invalid-token")

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": "invalid-token",
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_accept_from_member_with_other_user_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()
    other_user = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(other_user.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_accept_from_member_with_expired_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = ExpiredSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token has expired" == response.data["_error_message"]
    assert len(mail.outbox) == 0


def test_project_transfer_accept_from_member_with_valid_token_without_enough_slots(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_private_projects=0)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert len(mail.outbox) == 0
    project = Project.objects.get(pk=project.pk)
    assert project.owner.id == user_from.id
    assert project.transfer_token is not None


def test_project_transfer_accept_from_member_with_valid_token_without_enough_memberships_public_project_slots(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_memberships_public_projects=5)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=False)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    f.create_membership(project=project)
    f.create_membership(project=project)
    f.create_membership(project=project, user=None, email="test_1@email.com")
    f.create_membership(project=project, user=None, email="test_2@email.com")
    f.create_membership(project=project, user=None, email="test_3@email.com")

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert len(mail.outbox) == 0
    project = Project.objects.get(pk=project.pk)
    assert project.owner.id == user_from.id
    assert project.transfer_token is not None


def test_project_transfer_accept_from_member_with_valid_token_without_enough_memberships_private_project_slots(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_memberships_private_projects=5)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)
    project2 = f.create_project(owner=user_to, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)
    f.create_membership(project=project)
    f.create_membership(project=project, user=None, email="test_1@email.com")

    f.create_membership(user=user_from, project=project2, is_admin=True)
    f.create_membership(user=user_to, project=project2)
    f.create_membership(project=project2)
    f.create_membership(project=project2)
    f.create_membership(project=project2, user=None, email="test_1@email.com")

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert len(mail.outbox) == 0
    project = Project.objects.get(pk=project.pk)
    assert project.owner.id == user_from.id
    assert project.transfer_token is not None


def test_project_transfer_accept_from_admin_member_with_valid_token_with_enough_slots(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_private_projects=3)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=True)
    f.create_membership(user=None, project=project, email="test_1@email.com")

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user_from.email]
    project = Project.objects.get(pk=project.pk)
    assert project.owner.id == user_to.id
    assert project.transfer_token is None


def test_project_transfer_accept_from_no_admin_member_with_valid_token_with_enough_slots(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_private_projects=1)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    m = f.create_membership(user=user_to, project=project, is_admin=False)

    client.login(user_to)
    url = reverse("projects-transfer-accept", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }
    mail.outbox = []

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user_from.email]
    assert m.is_admin == False
    project = Project.objects.get(pk=project.pk)
    m = project.memberships.get(user=user_to)
    assert project.owner.id == user_to.id
    assert project.transfer_token is None
    assert m.is_admin == True


def test_project_transfer_validate_token_from_member_without_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {}

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400


def test_project_transfer_validate_token_from_member_with_invalid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    project = f.create_project(owner=user_from, transfer_token="invalid-token")

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {
        "token": "invalid-token",
    }

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]


def test_project_transfer_validate_token_from_member_with_other_user_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()
    other_user = f.UserFactory.create()

    signer = signing.TimestampSigner()
    token = signer.sign(other_user.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token is invalid" == response.data["_error_message"]


def test_project_transfer_validate_token_from_member_with_expired_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create()

    signer = ExpiredSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "Token has expired" == response.data["_error_message"]



def test_project_transfer_validate_token_from_admin_member_with_valid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_private_projects=1)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=True)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200


def test_project_transfer_validate_token_from_no_admin_member_with_valid_token(client):
    user_from = f.UserFactory.create()
    user_to = f.UserFactory.create(max_private_projects=1)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=False)

    client.login(user_to)
    url = reverse("projects-transfer-validate-token", kwargs={"pk": project.pk})

    data = {
        "token": token,
    }

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200


####################################################################################
# Test taiga.projects.services.projects.check_if_project_privacy_can_be_changed
####################################################################################

from taiga.projects.services.projects import (
    check_if_project_privacy_can_be_changed,
    ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS,
    ERROR_MAX_PUBLIC_PROJECTS,
    ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS,
    ERROR_MAX_PRIVATE_PROJECTS
)

# private to public

def test_private_project_cant_be_public_because_owner_doesnt_have_enough_slot_and_too_much_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 3

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS})


def test_private_project_cant_be_public_because_owner_doesnt_have_enough_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS})


def test_private_project_cant_be_public_because_too_much_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 3

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS})


def test_private_project_can_be_public_because_owner_has_enough_slot_and_project_has_enough_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = None

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = None

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


# public to private

def test_public_project_cant_be_private_because_owner_doesnt_have_enough_slot_and_too_much_members(client):
    project = f.create_project(is_private=False)
    project2 = f.create_project(is_private=True, owner=project.owner)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project2, user=project.owner)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 3

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS})


def test_public_project_cant_be_private_because_owner_doesnt_have_enough_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS})


def test_public_project_cant_be_private_because_too_much_members(client):
    project = f.create_project(is_private=False)
    project2 = f.create_project(is_private=True, owner=project.owner)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project2, user=project.owner)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 3

    assert (check_if_project_privacy_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS})


def test_public_project_can_be_private_because_owner_has_enough_slot_and_project_has_enough_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = None

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = None

    assert (check_if_project_privacy_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


####################################################################################
# test taiga.projects.services.projects.check_if_project_is_out_of_owner_limit
####################################################################################

from taiga.projects.services.projects import check_if_project_is_out_of_owner_limits

def test_private_project_when_owner_doesnt_have_enough_slot_and_too_much_members(client):
    project = f.create_project(is_private=True)
    project2 = f.create_project(is_private=True, owner=project.owner)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project2, user=project.owner)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_private_project_when_owner_doesnt_have_enough_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_private_project_when_too_much_members(client):
    project = f.create_project(is_private=True)
    project2 = f.create_project(is_private=True, owner=project.owner)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project2, user=project.owner)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_private_project_when_owner_has_enough_slot_and_project_has_enough_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_private_project_when_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = None

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_private_project_when_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_private_project_when_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = None

    assert check_if_project_is_out_of_owner_limits(project) == False


# public

def test_public_project_when_owner_doesnt_have_enough_slot_and_too_much_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_public_project_when_owner_doesnt_have_enough_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_public_project_when_too_much_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_public_project_when_owner_has_enough_slot_and_project_has_enough_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_public_project_when_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = None

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_public_project_when_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = 6

    assert check_if_project_is_out_of_owner_limits(project) == False


def test_public_project_when_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = None

    assert check_if_project_is_out_of_owner_limits(project) == False


####################################################################################
# test project deletion
####################################################################################

def test_delete_project_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-detail", args=(project.id,))
    client.login(user)

    #delete_project task should have been launched
    with mock.patch('taiga.projects.services.delete_project') as delete_project_mock:
        response = client.json.delete(url)
        assert response.status_code == 204
        project = Project.objects.get(id=project.id)
        assert project.owner == None
        assert project.memberships.count() == 0
        assert project.blocked_code == BLOCKED_BY_DELETING
        delete_project_mock.delay.assert_called_once_with(project.id)
    settings.CELERY_ENABLED = False


def test_delete_project_with_celery_disabled(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-detail", args=(project.id,))
    client.login(user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert Project.objects.filter(id=project.id).count() == 0


####################################################################################
# test project tags
####################################################################################

def test_create_tag(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-create-tag", args=(project.id,))
    client.login(user)
    data = {
        "tag": "newtag",
        "color": "#123123"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == [["newtag", "#123123"]]


def test_create_tag_without_color(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-create-tag", args=(project.id,))
    client.login(user)
    data = {
        "tag": "newtag",
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors[0][0] == "newtag"


def test_edit_tag_only_name(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag'1", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag'1"])
    task = f.TaskFactory.create(project=project, tags=["tag'1"])
    issue = f.IssueFactory.create(project=project, tags=["tag'1"])
    epic = f.EpicFactory.create(project=project, tags=["tag'1"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-edit-tag", args=(project.id,))
    client.login(user)
    data = {
        "from_tag": "tag'1",
        "to_tag": "renamed_tag'1"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == [["renamed_tag'1", "#123123"]]
    user_story = UserStory.objects.get(id=user_story.pk)
    assert user_story.tags == ["renamed_tag'1"]
    task = Task.objects.get(id=task.pk)
    assert task.tags == ["renamed_tag'1"]
    issue = Issue.objects.get(id=issue.pk)
    assert issue.tags == ["renamed_tag'1"]
    epic = Epic.objects.get(id=epic.pk)
    assert epic.tags == ["renamed_tag'1"]


def test_edit_tag_only_color(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])
    epic = f.EpicFactory.create(project=project, tags=["tag"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-edit-tag", args=(project.id,))
    client.login(user)
    data = {
        "from_tag": "tag",
        "color": "#AAABBB"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == [["tag", "#AAABBB"]]
    user_story = UserStory.objects.get(id=user_story.pk)
    assert user_story.tags == ["tag"]
    task = Task.objects.get(id=task.pk)
    assert task.tags == ["tag"]
    issue = Issue.objects.get(id=issue.pk)
    assert issue.tags == ["tag"]
    epic = Epic.objects.get(id=epic.pk)
    assert epic.tags == ["tag"]


def test_edit_tag(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])
    epic = f.EpicFactory.create(project=project, tags=["tag"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-edit-tag", args=(project.id,))
    client.login(user)
    data = {
        "from_tag": "tag",
        "to_tag": "renamed_tag",
        "color": "#AAABBB"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == [["renamed_tag", "#AAABBB"]]
    user_story = UserStory.objects.get(id=user_story.pk)
    assert user_story.tags == ["renamed_tag"]
    task = Task.objects.get(id=task.pk)
    assert task.tags == ["renamed_tag"]
    issue = Issue.objects.get(id=issue.pk)
    assert issue.tags == ["renamed_tag"]
    epic = Epic.objects.get(id=epic.pk)
    assert epic.tags == ["renamed_tag"]


def test_delete_tag(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag'1", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag'1"])
    task = f.TaskFactory.create(project=project, tags=["tag'1"])
    issue = f.IssueFactory.create(project=project, tags=["tag'1"])
    epic = f.EpicFactory.create(project=project, tags=["tag'1"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-delete-tag", args=(project.id,))
    client.login(user)
    data = {
        "tag": "tag'1"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == []
    user_story = UserStory.objects.get(id=user_story.pk)
    assert user_story.tags == []
    task = Task.objects.get(id=task.pk)
    assert task.tags == []
    issue = Issue.objects.get(id=issue.pk)
    assert issue.tags == []
    epic = Epic.objects.get(id=epic.pk)
    assert epic.tags == []


def test_mix_tags(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag'1", "#123123"), ("tag2", "#123123"), ("tag3", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag'1", "tag3"])
    task = f.TaskFactory.create(project=project, tags=["tag2", "tag3"])
    issue = f.IssueFactory.create(project=project, tags=["tag'1", "tag2", "tag3"])
    epic = f.EpicFactory.create(project=project, tags=["tag'1", "tag2", "tag3"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-mix-tags", args=(project.id,))
    client.login(user)
    data = {
        "from_tags": ["tag'1", "tag2"],
        "to_tag": "tag2"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert set(["tag2", "tag3"]) == set(dict(project.tags_colors).keys())
    user_story = UserStory.objects.get(id=user_story.pk)
    assert set(user_story.tags) == set(["tag2", "tag3"])
    task = Task.objects.get(id=task.pk)
    assert set(task.tags) == set(["tag2", "tag3"])
    issue = Issue.objects.get(id=issue.pk)
    assert set(issue.tags) == set(["tag2", "tag3"])
    epic = Epic.objects.get(id=epic.pk)
    assert set(epic.tags) == set(["tag2", "tag3"])


def test_color_tags_project_fired_on_element_create():
    user_story = f.UserStoryFactory.create(tags=["tag"])
    project = Project.objects.get(id=user_story.project.id)
    assert project.tags_colors == [["tag", None]]


def test_color_tags_project_fired_on_element_update():
    user_story = f.UserStoryFactory.create()
    user_story.tags = ["tag"]
    user_story.save()
    project = Project.objects.get(id=user_story.project.id)
    assert ["tag", None] in project.tags_colors


def test_color_tags_project_fired_on_element_update_respecting_color():
    project = f.ProjectFactory.create(tags_colors=[["tag", "#123123"]])
    user_story = f.UserStoryFactory.create(project=project)
    user_story.tags = ["tag"]
    user_story.save()
    project = Project.objects.get(id=user_story.project.id)
    assert ["tag", "#123123"] in project.tags_colors


####################################################################################
# test project duplication
####################################################################################

def test_duplicate_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(
        owner=user,
        is_looking_for_people=True,
        looking_for_people_note="Looking lookin",
    )
    project.tags = ["tag1", "tag2"]
    project.tags_colors = [["t1", "#abcbca"], ["t2", "#aaabbb"]]

    project.default_epic_status = f.EpicStatusFactory.create(project=project)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_points = f.PointsFactory.create(project=project)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)

    f.EpicCustomAttributeFactory(project=project)
    f.UserStoryCustomAttributeFactory(project=project)
    f.TaskCustomAttributeFactory(project=project)
    f.IssueCustomAttributeFactory(project=project)

    project.save()

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    extra_membership = f.MembershipFactory.create(project=project, is_admin=True, role__project=project)
    membership = f.MembershipFactory.create(project=project, role=role)
    url = reverse("projects-duplicate", args=(project.id,))

    data = {
        "name": "test",
        "description": "description",
        "is_private": True,
        "users": [{
            "id": extra_membership.user.id
        }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201

    new_project = Project.objects.get(id=response.data["id"])

    assert new_project.owner_id == user.id
    owner_membership = new_project.memberships.get(user_id=user.id)
    assert owner_membership.user_id == user.id
    assert owner_membership.is_admin == True
    assert project.memberships.get(user_id=extra_membership.user.id).role.slug == extra_membership.role.slug
    assert set(project.tags) == set(new_project.tags)
    assert set(dict(project.tags_colors).keys()) == set(dict(new_project.tags_colors).keys())

    attributes = [
        "is_epics_activated", "is_backlog_activated", "is_kanban_activated", "is_wiki_activated",
        "is_issues_activated", "videoconferences", "videoconferences_extra_data",
        "is_looking_for_people", "looking_for_people_note", "is_private"
    ]

    for attr in attributes:
        assert getattr(project, attr) == getattr(new_project, attr)

    fk_attributes = [
        "default_epic_status", "default_us_status", "default_task_status", "default_issue_status",
        "default_issue_type", "default_points", "default_priority", "default_severity",
    ]

    for attr in fk_attributes:
        assert getattr(project, attr).name == getattr(new_project, attr).name

    related_attributes = [
        "epic_statuses", "us_statuses", "task_statuses","issue_statuses",
        "issue_types", "points", "priorities", "severities",
        "epiccustomattributes", "userstorycustomattributes", "taskcustomattributes", "issuecustomattributes",
        "roles"
    ]
    for attr in related_attributes:
        from_names = set(getattr(project, attr).all().values_list("name", flat=True))
        to_names = set(getattr(new_project, attr).all().values_list("name", flat=True))
        assert from_names == to_names

    timeline = list(get_project_timeline(new_project))
    assert len(timeline) == 2
    assert timeline[0].event_type == "projects.project.create"
    assert timeline[1].event_type == "projects.membership.create"


def test_duplicate_private_project_without_enough_private_projects_slots(client):
    user = f.UserFactory.create(max_private_projects=0)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(user=user, project=project, is_admin=True)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": True,
        "users": []
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "can't have more private projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "True"


def test_duplicate_private_project_without_enough_memberships_slots(client):
    user = f.UserFactory.create(max_memberships_private_projects=1)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(user=user, project=project, is_admin=True, role__project=project)
    extra_membership = f.MembershipFactory(project=project, role__project=project)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": True,
        "users": [{
            "id": extra_membership.user_id
        }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "current limit of memberships" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "2"
    assert response["Taiga-Info-Project-Is-Private"] == "True"


def test_duplicate_private_project_without_enough_memberships_slots_for_existen_projects(client):
    user = f.UserFactory.create(max_memberships_private_projects=3)
    project = f.ProjectFactory.create()
    extra_membership = f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    f.MembershipFactory(user=user, project=project, is_admin=True)
    project2 = f.ProjectFactory.create(owner=user, is_private=True)
    f.MembershipFactory(user=user, project=project2, is_admin=True)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": True,
        "users": [{
            "id": extra_membership.user_id
        }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "current limit of memberships" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "4"
    assert response["Taiga-Info-Project-Is-Private"] == "True"


def test_duplicate_public_project_without_enough_public_projects_slots(client):
    user = f.UserFactory.create(max_public_projects=0)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(user=user, project=project, is_admin=True)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": False,
        "users": []
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "can't have more public projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_duplicate_public_project_without_enough_memberships_slots(client):
    user = f.UserFactory.create(max_memberships_public_projects=1)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(user=user, project=project, is_admin=True, role__project=project)
    extra_membership = f.MembershipFactory(project=project, role__project=project)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": False,
        "users": [
            {"id": extra_membership.user_id},
        ]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "current limit of memberships" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "2"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_duplicate_public_project_without_enough_memberships_slots_for_existen_projects(client):
    user = f.UserFactory.create(max_memberships_public_projects=3)
    project = f.ProjectFactory.create()
    extra_membership = f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    f.MembershipFactory(user=user, project=project, is_admin=True)
    project2 = f.ProjectFactory.create(owner=user, is_private=False)
    f.MembershipFactory(user=user, project=project2, is_admin=True)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": False,
        "users": [{
            "id": extra_membership.user_id
        }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "current limit of memberships" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "4"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_duplicate_public_project_without_enough_memberships_slots_for_existen_projects_with_invitations(client):
    user = f.UserFactory.create(max_memberships_public_projects=3)
    project = f.ProjectFactory.create()
    extra_membership = f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    f.MembershipFactory(user=user, project=project, is_admin=True)
    f.MembershipFactory(project=project, email="test@email.com", user=None)
    project2 = f.ProjectFactory.create(owner=user, is_private=False)
    f.MembershipFactory(user=user, project=project2, is_admin=True)
    f.MembershipFactory(project=project2)
    f.MembershipFactory(project=project2, email="test@email.com", user=None)

    url = reverse("projects-duplicate", args=(project.id,))
    data = {
        "name": "test",
        "description": "description",
        "is_private": False,
        "users": [{
            "id": extra_membership.user_id
        }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert "current limit of memberships" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "4"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


####################################################################################
# test due dates
####################################################################################

# User story

def test_create_us_default_due_dates(client):
    project = f.create_project()

    us_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    creation_template = project.creation_template
    creation_template.us_duedates = us_duedates
    creation_template.save()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('userstory-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert project.us_duedates.count() == 1


def test_prevent_create_us_default_due_dates_when_already_exists(client):
    us_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, us_duedates=us_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('userstory-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert project.us_duedates.count() == 1


def test_prevent_delete_us_default_due_dates(client):
    us_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, us_duedates=us_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('userstory-due-dates-detail',
                  kwargs={"pk": project.us_duedates.last().pk})
    client.login(project.owner)

    response = client.json.delete(url)

    assert response.status_code == 400
    assert project.us_duedates.count() == 1


# Task

def test_create_task_default_due_dates(client):
    project = f.create_project()

    task_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    creation_template = project.creation_template
    creation_template.task_duedates = task_duedates
    creation_template.save()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('task-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert project.task_duedates.count() == 1


def test_prevent_create_task_default_due_dates_when_already_exists(client):
    task_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, task_duedates=task_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('task-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert project.task_duedates.count() == 1


def test_prevent_delete_task_default_due_dates(client):
    task_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, task_duedates=task_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('task-due-dates-detail',
                  kwargs={"pk": project.task_duedates.last().pk})
    client.login(project.owner)

    response = client.json.delete(url)

    assert response.status_code == 400
    assert project.task_duedates.count() == 1


# Issue

def test_create_issue_default_due_dates(client):
    project = f.create_project()

    issue_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    creation_template = project.creation_template
    creation_template.issue_duedates = issue_duedates
    creation_template.save()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('issue-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    assert project.issue_duedates.count() == 1


def test_prevent_create_issue_default_due_dates_when_already_exists(client):
    issue_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, issue_duedates=issue_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('issue-due-dates-create-default')
    data = {"project_id": project.pk}
    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert project.issue_duedates.count() == 1


def test_prevent_delete_issue_default_due_dates(client):
    issue_duedates = [{
        "name": 'Default',
        "by_default": True,
        'color': '#0000',
        'days_to_due': None,
        'order': 0,
    }]
    f.ProjectTemplateFactory.create(
        slug=settings.DEFAULT_PROJECT_TEMPLATE, issue_duedates=issue_duedates)
    project = f.create_project()

    f.MembershipFactory(user=project.owner, project=project, is_admin=True)
    url = reverse('issue-due-dates-detail',
                  kwargs={"pk": project.issue_duedates.last().pk})
    client.login(project.owner)

    response = client.json.delete(url)

    assert response.status_code == 400
    assert project.issue_duedates.count() == 1


####################################################################################
# test swimlanes
####################################################################################

def test_create_first_swimlane_and_assign_to_uss(client):
    project = f.create_project()
    membership = f.create_membership(project=project, is_admin=True)
    us = f.create_userstory(owner=membership.user,
                            project=project)
    assert us.swimlane is None
    assert project.default_swimlane is None

    url = reverse('swimlanes-list')
    data = {
        "project": project.id,
        "name": "Swimlane 1"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))
    us.refresh_from_db()
    project.refresh_from_db()

    assert response.status_code == 201
    assert project.swimlanes.count() == 1
    assert project.default_swimlane_id == us.swimlane_id
    assert us.swimlane is not None


def test_create_second_swimlane(client):
    # given a first swimlane related to a project
    project = f.create_project()
    membership = f.create_membership(project=project, is_admin=True)
    us = f.create_userstory(owner=membership.user,
                            project=project)

    url = reverse('swimlanes-list')
    data = {
        "project": project.id,
        "name": "Swimlane 1"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))
    swimlane_1_id = json.loads(response.content)['id']

    project.refresh_from_db()
    assert project.default_swimlane_id == swimlane_1_id

    # when: create second swimlane
    data = {
        "project": project.id,
        "name": "Swimlane 2"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))
    swimlane_2_id = json.loads(response.content)['id']
    swimlane_2 = Swimlane.objects.get(pk=swimlane_2_id)

    us.refresh_from_db()
    project.refresh_from_db()

    # then
    assert response.status_code == 201
    assert project.swimlanes.count() == 2
    assert project.default_swimlane_id == swimlane_1_id
    assert swimlane_2.user_stories.count() == 0
    assert us.swimlane.id == swimlane_1_id


def test_swimlane_bulk_update_order(client):
    project = f.create_project()
    membership = f.create_membership(project=project, is_admin=True)
    us1 = f.create_userstory(subject='us1',
                             owner=membership.user,
                             project=project)
    us2 = f.create_userstory(subject='us2',
                             owner=membership.user,
                             project=project)

    url = reverse('swimlanes-list')
    data = {
        "project": project.id,
        "name": "S1"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))

    project.refresh_from_db()
    swimlane1 = project.swimlanes.filter(name='S1').first()

    # both uss now belong to the first new swimlane
    assert swimlane1.user_stories.count() == 2

    # us without swimlane
    us3 = f.create_userstory(subject='us3',
                             owner=membership.user,
                             project=project)
    data = {
        "project": project.id,
        "name": "S2"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))

    project.refresh_from_db()
    swimlane2 = project.swimlanes.filter(name='S2').first()
    us4 = f.create_userstory(subject='us4',
                             owner=membership.user,
                             project=project,
                             swimlane=swimlane2)
    us5 = f.create_userstory(subject='us5',
                             owner=membership.user,
                             project=project,
                             swimlane=swimlane2)

    # both new user stories belong to the second swimlane
    assert swimlane2.user_stories.count() == 2

    # In this moment, they are arranged like:
    # us1, us2, us4, us5, us3
    project.refresh_from_db()
    ordered_uss = project.user_stories.all().order_by('swimlane__order', 'kanban_order')

    assert ordered_uss[0].subject == 'us1'
    assert ordered_uss[1].subject == 'us2'
    assert ordered_uss[2].subject == 'us4'
    assert ordered_uss[3].subject == 'us5'
    assert ordered_uss[4].subject == 'us3'

    # After arranging the swimlanes, they should be like:
    # us4, us5, us1, us2, us3
    url = reverse('swimlanes-bulk-update-order')
    data = {
        "project": project.id,
        "bulk_swimlanes": [
            [swimlane2.id, 0],
            [swimlane1.id, 1],
        ]
    }
    response = client.json.post(url, json.dumps(data))

    project.refresh_from_db()
    ordered_uss = project.user_stories.all().order_by('swimlane__order', 'kanban_order')

    assert ordered_uss[0].subject == 'us4'
    assert ordered_uss[1].subject == 'us5'
    assert ordered_uss[2].subject == 'us1'
    assert ordered_uss[3].subject == 'us2'
    assert ordered_uss[4].subject == 'us3'


def test_delete_swimlane(client):
    project = f.create_project()
    membership = f.create_membership(project=project, is_admin=True)
    us1 = f.create_userstory(subject='us1',
                             owner=membership.user,
                             project=project)
    us2 = f.create_userstory(subject='us2',
                             owner=membership.user,
                             project=project)

    url = reverse('swimlanes-list')
    data = {
        "project": project.id,
        "name": "S1"
    }
    client.login(membership.user)
    response = client.json.post(url, json.dumps(data))

    project.refresh_from_db()
    swimlane1 = project.swimlanes.filter(name='S1').first()

    # us without swimlane
    us3 = f.create_userstory(subject='us3',
                             owner=membership.user,
                             project=project)

    data = {
        "project": project.id,
        "name": "S2"
    }
    response = client.json.post(url, json.dumps(data))

    project.refresh_from_db()
    swimlane2 = project.swimlanes.filter(name='S2').first()

    # set S2 as default swimlane
    project.default_swimlane = swimlane2
    project.save()

    us4 = f.create_userstory(subject='us4',
                             owner=membership.user,
                             project=project,
                             swimlane=swimlane2)
    us5 = f.create_userstory(subject='us5',
                             owner=membership.user,
                             project=project,
                             swimlane=swimlane2)

    url = reverse('swimlanes-detail', kwargs={"pk": swimlane1.id})

    # force an error with swimlane=None
    response = client.json.delete(url)
    assert response.status_code == 400
    assert response.data['_error_message'] == "Cannot set swimlane to None if there are available swimlanes"

    # force an error with swimlane=non_existing
    url = reverse('swimlanes-detail',
            kwargs={"pk": swimlane1.id}) + "?moveTo=300"
    response = client.json.delete(url)
    assert response.status_code == 404
    assert response.data['_error_message'] == "No Swimlane matches the given query."

    # In this moment, they are arranged like:
    # us1, us2, us3, us4, us5
    # After deleting swimlane1, they should be like:
    # us3, us4, us5, us1, us2
    url = reverse('swimlanes-detail',
            kwargs={"pk": swimlane1.id}) + "?moveTo={}".format(swimlane2.id)
    response = client.json.delete(url)

    assert response.status_code == 204

    project.refresh_from_db()
    ordered_uss = project.user_stories.all().order_by('kanban_order')

    assert ordered_uss[0].subject == 'us3'
    assert ordered_uss[0].swimlane is None
    assert ordered_uss[1].subject == 'us4'
    assert ordered_uss[1].swimlane == swimlane2
    assert ordered_uss[2].subject == 'us5'
    assert ordered_uss[2].swimlane == swimlane2
    assert ordered_uss[3].subject == 'us1'
    assert ordered_uss[3].swimlane == swimlane2
    assert ordered_uss[4].subject == 'us2'
    assert ordered_uss[4].swimlane == swimlane2


def test_prevent_delete_swimlane_if_is_the_default_and_there_are_more_than_one(client):
    project = f.create_project()
    membership = f.create_membership(project=project, is_admin=True)
    sw1 = f.create_swimlane(project=project)
    sw2 = f.create_swimlane(project=project)

    project.refresh_from_db()
    assert project.default_swimlane_id == sw1.id

    client.login(membership.user)

    # force an error trying to delete sw1 (the default swimlane)
    url = reverse('swimlanes-detail',
            kwargs={"pk": sw1.id}) + "?moveTo={}".format(sw2.id)
    response = client.json.delete(url)
    assert response.status_code == 400
    assert '_error_message' in response.data

    # there is no problem removing not default swimlanes
    url = reverse('swimlanes-detail',
            kwargs={"pk": sw2.id}) + "?moveTo={}".format(sw1.id)
    response = client.json.delete(url)
    assert response.status_code == 204

    # Now sw1 is the only one, so you can delete it
    url = reverse('swimlanes-detail', kwargs={"pk": sw1.id})
    response = client.json.delete(url)
    assert response.status_code == 204

    project.refresh_from_db()
    assert project.default_swimlane_id is None


def test_swimlane_userstory_statuses_creation_and_set_default_wip_limits_for_first_swimlane_creation_only(client):
    project = f.create_project()
    project.default_us_status.wip_limit = 42
    project.default_us_status.save()

    swimlane1 = f.create_swimlane(project=project)

    assert swimlane1.statuses.count() == 1
    assert swimlane1.statuses.first().wip_limit == 42

    swimlane2 = f.create_swimlane(project=project)

    assert swimlane2.statuses.count() == 1
    assert swimlane2.statuses.first().wip_limit is None


def test_swimlane_userstory_statuses_creation_when_a_new_user_story_status_is_created(client):
    project = f.create_project()

    project.default_us_status.wip_limits = 42
    project.default_us_status.save()

    swimlane1 = f.create_swimlane(project=project)

    f.UserStoryStatusFactory(project=project, wip_limit=24)

    assert swimlane1.statuses.count() == 2
    assert swimlane1.statuses.all()[1].wip_limit == 24

    swimlane2 = f.create_swimlane(project=project)

    f.UserStoryStatusFactory(project=project, wip_limit=32)

    assert swimlane2.statuses.count() == 3
    assert swimlane2.statuses.all()[2].wip_limit is None
