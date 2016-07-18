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

from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files import File
from django.core import mail
from django.core import signing

from taiga.base.utils import json
from taiga.projects.services import stats as stats_services
from taiga.projects.history.services import take_snapshot
from taiga.permissions.choices import ANON_PERMISSIONS
from taiga.projects.models import Project
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.issues.models import Issue
from taiga.projects.choices import BLOCKED_BY_DELETING

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


def test_get_project_by_slug(client):
    project = f.create_project()
    url = reverse("projects-detail", kwargs={"pk": project.slug})

    response = client.json.get(url)
    assert response.status_code == 404

    client.login(project.owner)
    response = client.json.get(url)
    assert response.status_code == 404


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

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is True

    us_status.is_closed = False
    us_status.save()

    user_story = user_story.__class__.objects.get(pk=user_story.pk)
    assert user_story.is_closed is False


def test_task_status_is_closed_changed_recalc_us_is_closed(client):
    us_status = f.UserStoryStatusFactory()
    user_story = f.UserStoryFactory.create(project=us_status.project, status=us_status)
    task_status = f.TaskStatusFactory.create(project=us_status.project, is_closed=False)
    task = f.TaskFactory.create(project=us_status.project, status=task_status, user_story=user_story)

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
    assert response.data["name"][0] == "Name duplicated for the project"


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
    project = Project.objects.get(id=project.id)
    assert project.default_points.id == p2.id


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
    f.create_membership(project=project)
    f.create_membership(project=project)
    f.create_membership(project=project)

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

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project)

    f.create_membership(project=project)
    f.create_membership(project=project)
    f.create_membership(project=project)
    f.create_membership(project=project)
    f.create_membership(project=project)

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
    user_to = f.UserFactory.create(max_private_projects=1)

    signer = signing.TimestampSigner()
    token = signer.sign(user_to.id)
    project = f.create_project(owner=user_from, transfer_token=token, is_private=True)

    f.create_membership(user=user_from, project=project, is_admin=True)
    f.create_membership(user=user_to, project=project, is_admin=True)

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
# Test taiga.projects.services.projects.check_if_project_privacity_can_be_changed
####################################################################################

from taiga.projects.services.projects import (
    check_if_project_privacity_can_be_changed,
    ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS,
    ERROR_MAX_PUBLIC_PROJECTS,
    ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS,
    ERROR_MAX_PRIVATE_PROJECTS
)

# private to public

def test_private_project_cant_be_public_because_owner_doesnt_have_enought_slot_and_too_much_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 3

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS})


def test_private_project_cant_be_public_because_owner_doesnt_have_enought_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS})


def test_private_project_cant_be_public_because_too_much_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 3

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS})


def test_private_project_can_be_public_because_owner_has_enought_slot_and_project_has_enought_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = None

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = None
    project.owner.max_memberships_public_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_private_project_can_be_public_because_project_has_unlimited_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 2
    project.owner.max_memberships_public_projects = None

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


# public to private

def test_public_project_cant_be_private_because_owner_doesnt_have_enought_slot_and_too_much_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 3

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS})


def test_public_project_cant_be_private_because_owner_doesnt_have_enought_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS})


def test_public_project_cant_be_private_because_too_much_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 3

    assert (check_if_project_privacity_can_be_changed(project) ==
            {'can_be_updated': False, 'reason': ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS})


def test_public_project_can_be_private_because_owner_has_enought_slot_and_project_has_enought_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_owner_has_unlimited_slot_and_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = None

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_owner_has_unlimited_slot(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = None
    project.owner.max_memberships_private_projects = 6

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


def test_public_project_can_be_private_because_project_has_unlimited_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = None

    assert (check_if_project_privacity_can_be_changed(project) == {'can_be_updated': True, 'reason': None})


####################################################################################
# Test taiga.projects.services.projects.check_if_project_is_out_of_owner_limit
####################################################################################

from taiga.projects.services.projects import check_if_project_is_out_of_owner_limits

def test_private_project_when_owner_doesnt_have_enought_slot_and_too_much_members(client):
    project = f.create_project(is_private=True)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 0
    project.owner.max_memberships_private_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_private_project_when_owner_doesnt_have_enought_slot(client):
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
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_private_projects = 2
    project.owner.max_memberships_private_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_private_project_when_owner_has_enought_slot_and_project_has_enought_members(client):
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

def test_public_project_when_owner_doesnt_have_enought_slot_and_too_much_members(client):
    project = f.create_project(is_private=False)
    f.MembershipFactory(project=project, user=project.owner)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)
    f.MembershipFactory(project=project)

    project.owner.max_public_projects = 0
    project.owner.max_memberships_public_projects = 3

    assert check_if_project_is_out_of_owner_limits(project) == True


def test_public_project_when_owner_doesnt_have_enought_slot(client):
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


def test_public_project_when_owner_has_enought_slot_and_project_has_enought_members(client):
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


def test_delete_project_with_celery_disabled(client, settings):
    settings.CELERY_ENABLED = False

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-detail", args=(project.id,))
    client.login(user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert Project.objects.filter(id=project.id).count() == 0


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
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-edit-tag", args=(project.id,))
    client.login(user)
    data = {
        "from_tag": "tag",
        "to_tag": "renamed_tag"
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200
    project = Project.objects.get(id=project.pk)
    assert project.tags_colors == [["renamed_tag", "#123123"]]
    user_story = UserStory.objects.get(id=user_story.pk)
    assert user_story.tags == ["renamed_tag"]
    task = Task.objects.get(id=task.pk)
    assert task.tags == ["renamed_tag"]
    issue = Issue.objects.get(id=issue.pk)
    assert issue.tags == ["renamed_tag"]


def test_edit_tag_only_color(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])

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


def test_edit_tag(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])

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


def test_delete_tag(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag"])
    task = f.TaskFactory.create(project=project, tags=["tag"])
    issue = f.IssueFactory.create(project=project, tags=["tag"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-delete-tag", args=(project.id,))
    client.login(user)
    data = {
        "tag": "tag"
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


def test_mix_tags(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user, tags_colors=[("tag1", "#123123"), ("tag2", "#123123"), ("tag3", "#123123")])
    user_story = f.UserStoryFactory.create(project=project, tags=["tag1", "tag3"])
    task = f.TaskFactory.create(project=project, tags=["tag2", "tag3"])
    issue = f.IssueFactory.create(project=project, tags=["tag1", "tag2", "tag3"])

    role = f.RoleFactory.create(project=project, permissions=["view_project"])
    membership = f.MembershipFactory.create(project=project, user=user, role=role, is_admin=True)
    url = reverse("projects-mix-tags", args=(project.id,))
    client.login(user)
    data = {
        "from_tags": ["tag1", "tag2"],
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
