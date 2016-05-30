# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import pytest
import base64

from django.apps import apps
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile

from taiga.base.utils import json
from taiga.export_import import services
from taiga.export_import.exceptions import  TaigaImportError
from taiga.projects.models import Project, Membership
from taiga.projects.issues.models import Issue
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.wiki.models import WikiPage

from .. import factories as f
from ..utils import DUMMY_BMP_DATA

pytestmark = pytest.mark.django_db



#######################################################
## test api/v1/importer
#######################################################

def test_invalid_project_import(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_project_import_without_extra_data(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{"name": "Role"}],
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    must_empty_children = [
        "issues", "user_stories", "us_statuses", "wiki_pages", "priorities",
        "severities", "milestones", "points", "issue_types", "task_statuses",
        "issue_statuses", "wiki_links",
    ]
    assert all(map(lambda x: len(response.data[x]) == 0, must_empty_children))
    assert response.data["owner"] == user.email
    assert response.data["watchers"] == [user.email, user_watching.email]


def test_valid_project_without_enough_public_projects_slots(client):
    user = f.UserFactory.create(max_public_projects=0)

    url = reverse("importer-list")
    data = {
        "slug": "public-project-without-slots",
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{"name": "Role"}],
        "is_private": False
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more public projects" in response.data["_error_message"]
    assert Project.objects.filter(slug="public-project-without-slots").count() == 0
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "False"


def test_valid_project_without_enough_private_projects_slots(client):
    user = f.UserFactory.create(max_private_projects=0)

    url = reverse("importer-list")
    data = {
        "slug": "private-project-without-slots",
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{"name": "Role"}],
        "is_private": True
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 400
    assert "can't have more private projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "True"
    assert Project.objects.filter(slug="private-project-without-slots").count() == 0


def test_valid_project_with_enough_public_projects_slots(client):
    user = f.UserFactory.create(max_public_projects=1)

    url = reverse("importer-list")
    data = {
        "slug": "public-project-with-slots",
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{"name": "Role"}],
        "is_private": False
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert Project.objects.filter(slug="public-project-with-slots").count() == 1


def test_valid_project_with_enough_private_projects_slots(client):
    user = f.UserFactory.create(max_private_projects=1)

    url = reverse("importer-list")
    data = {
        "slug": "private-project-with-slots",
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{"name": "Role"}],
        "is_private": True
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201
    assert Project.objects.filter(slug="private-project-with-slots").count() == 1


def test_valid_project_import_with_not_existing_memberships(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "memberships": [{
            "email": "bad@email.com",
            "role": "Role",
        }],
        "roles": [{"name": "Role"}]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    # The new membership and the owner membership
    assert len(response.data["memberships"]) == 2


def test_valid_project_import_with_membership_uuid_rewrite(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "memberships": [{
            "email": "with-uuid@email.com",
            "role": "Role",
            "token": "123",
        }],
        "roles": [{"name": "Role"}]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert Membership.objects.filter(email="with-uuid@email.com", token="123").count() == 0


def test_valid_project_import_with_extra_data(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{
            "permissions": [],
            "name": "Test"
        }],
        "us_statuses": [{
            "name": "Test"
        }],
        "severities": [{
            "name": "Test"
        }],
        "priorities": [{
            "name": "Test"
        }],
        "points": [{
            "name": "Test"
        }],
        "issue_types": [{
            "name": "Test"
        }],
        "task_statuses": [{
            "name": "Test"
        }],
        "issue_statuses": [{
            "name": "Test"
        }],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    must_empty_children = [
        "issues", "user_stories", "wiki_pages", "milestones",
        "wiki_links",
    ]

    must_one_instance_children = [
        "roles", "us_statuses", "severities", "priorities", "points",
        "issue_types", "task_statuses", "issue_statuses", "memberships",
    ]

    assert all(map(lambda x: len(response.data[x]) == 0, must_empty_children))
    # Allwais is created at least the owner membership
    assert all(map(lambda x: len(response.data[x]) == 1, must_one_instance_children))
    assert response.data["owner"] == user.email


def test_invalid_project_import_without_roles(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 2
    assert Project.objects.filter(slug="imported-project").count() == 0

def test_invalid_project_import_with_extra_data(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{
            "permissions": [],
            "name": "Test"
        }],
        "us_statuses": [{}],
        "severities": [{}],
        "priorities": [{}],
        "points": [{}],
        "issue_types": [{}],
        "task_statuses": [{}],
        "issue_statuses": [{}],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 7
    assert Project.objects.filter(slug="imported-project").count() == 0


def test_valid_project_import_with_custom_attributes(client):
    user = f.UserFactory.create()

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{
            "permissions": [],
            "name": "Test"
        }],
        "userstorycustomattributes": [{
            "name": "custom attribute example 1",
            "description": "short description 1",
            "order": 1
        }],
        "taskcustomattributes": [{
            "name": "custom attribute example 1",
            "description": "short description 1",
            "order": 1
        }],
        "issuecustomattributes": [{
            "name": "custom attribute example 1",
            "description": "short description 1",
            "order": 1
        }]
    }

    must_empty_children = ["issues", "user_stories", "wiki_pages", "milestones", "wiki_links"]
    must_one_instance_children = ["userstorycustomattributes", "taskcustomattributes", "issuecustomattributes"]

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert all(map(lambda x: len(response.data[x]) == 0, must_empty_children))
    # Allwais is created at least the owner membership
    assert all(map(lambda x: len(response.data[x]) == 1, must_one_instance_children))
    assert response.data["owner"] == user.email


def test_invalid_project_import_with_custom_attributes(client):
    user = f.UserFactory.create()

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{
            "permissions": [],
            "name": "Test"
        }],
        "userstorycustomattributes": [{ }],
        "taskcustomattributes": [{ }],
        "issuecustomattributes": [{ }]
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 3
    assert Project.objects.filter(slug="imported-project").count() == 0


#######################################################
## tes api/v1/importer/milestone
#######################################################

def test_invalid_milestone_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_milestone_import(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {
        "name": "Imported milestone",
        "estimated_start": "2014-10-10",
        "estimated_finish": "2014-10-20",
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["watchers"] == [user_watching.email]

def test_milestone_import_duplicated_milestone(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {
        "name": "Imported milestone",
        "estimated_start": "2014-10-10",
        "estimated_finish": "2014-10-20",
    }
    # We create twice the same milestone
    response = client.json.post(url, json.dumps(data))
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert response.data["milestones"][0]["name"][0] == "Name duplicated for the project"



#######################################################
## tes api/v1/importer/us
#######################################################

def test_invalid_us_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_us_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Test"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None


def test_valid_us_import_with_extra_data(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported us",
        "description": "Imported us",
        "attachments": [{
            "owner": user.email,
            "attached_file": {
                "name": "imported attachment",
                "data": base64.b64encode(b"TEST").decode("utf-8")
            }
        }],
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None
    assert response.data["watchers"] == [user_watching.email]


def test_invalid_us_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported us",
        "description": "Imported us",
        "attachments": [{}],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1
    assert UserStory.objects.filter(subject="Imported us").count() == 0


def test_invalid_us_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported us",
        "description": "Imported us",
        "status": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1


#######################################################
## tes api/v1/importer/task
#######################################################

def test_invalid_task_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_task_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Test"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None


def test_valid_task_import_with_custom_attributes_values(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    custom_attr = f.TaskCustomAttributeFactory(project=project)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Test Custom Attrs Values Tasks",
        "custom_attributes_values": {
            custom_attr.name: "test_value"
        }
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    custom_attributes_values = apps.get_model("custom_attributes.TaskCustomAttributesValues").objects.get(
                                                        task__subject=response.data["subject"])
    assert custom_attributes_values.attributes_values == {str(custom_attr.id): "test_value"}


def test_valid_task_import_with_extra_data(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "attachments": [{
            "owner": user.email,
            "attached_file": {
                "name": "imported attachment",
                "data": base64.b64encode(b"TEST").decode("utf-8")
            }
        }],
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None
    assert response.data["watchers"] == [user_watching.email]


def test_invalid_task_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "attachments": [{}],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1
    assert Task.objects.filter(subject="Imported task").count() == 0


def test_invalid_task_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "status": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1


def test_valid_task_with_user_story(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    us = f.UserStoryFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "user_story": us.ref
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert us.tasks.all().count() == 1


#######################################################
## tes api/v1/importer/issue
#######################################################

def test_invalid_issue_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_user_story_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "finish_date": "2014-10-24T00:00:00+0000"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["subject"] == "Imported issue"
    assert response.data["finish_date"] == "2014-10-24T00:00:00+0000"


def test_valid_user_story_import_with_custom_attributes_values(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    custom_attr = f.UserStoryCustomAttributeFactory(project=project)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Test Custom Attrs Values User Story",
        "custom_attributes_values": {
            custom_attr.name: "test_value"
        }
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    custom_attributes_values = apps.get_model("custom_attributes.UserStoryCustomAttributesValues").objects.get(
                                                        user_story__subject=response.data["subject"])
    assert custom_attributes_values.attributes_values == {str(custom_attr.id): "test_value"}


def test_valid_issue_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Test"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None


def test_valid_issue_import_with_custom_attributes_values(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    custom_attr = f.IssueCustomAttributeFactory(project=project)

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Test Custom Attrs Values Issues",
        "custom_attributes_values": {
            custom_attr.name: "test_value"
        }
    }

    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    custom_attributes_values = apps.get_model("custom_attributes.IssueCustomAttributesValues").objects.get(
                                                        issue__subject=response.data["subject"])
    assert custom_attributes_values.attributes_values == {str(custom_attr.id): "test_value"}


def test_valid_issue_import_with_extra_data(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "finished_date": "2014-10-24T00:00:00+0000",
        "attachments": [{
            "owner": user.email,
            "attached_file": {
                "name": "imported attachment",
                "data": base64.b64encode(b"TEST").decode("utf-8")
            }
        }],
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    assert response.data["owner"] == user.email
    assert response.data["ref"] is not None
    assert response.data["finished_date"] == "2014-10-24T00:00:00+0000"
    assert response.data["watchers"] == [user_watching.email]


def test_invalid_issue_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "attachments": [{}],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1
    assert Issue.objects.filter(subject="Imported issue").count() == 0


def test_invalid_issue_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    project.default_issue_type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = f.IssueStatusFactory.create(project=project)
    project.default_severity = f.SeverityFactory.create(project=project)
    project.default_priority = f.PriorityFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "status": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "priority": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "severity": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "type": "Not valid"
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1


#######################################################
## tes api/v1/importer/wiki-page
#######################################################

def test_invalid_wiki_page_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_wiki_page_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {
        "slug": "imported-wiki-page",
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["owner"] == user.email


def test_valid_wiki_page_import_with_extra_data(client):
    user = f.UserFactory.create()
    user_watching = f.UserFactory.create(email="testing@taiga.io")
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {
        "slug": "imported-wiki-page",
        "content": "Imported wiki_page",
        "attachments": [{
            "owner": user.email,
            "attached_file": {
                "name": "imported attachment",
                "data": base64.b64encode(b"TEST").decode("utf-8")
            }
        }],
        "watchers": ["testing@taiga.io"]
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    assert response.data["owner"] == user.email
    assert response.data["watchers"] == [user_watching.email]


def test_invalid_wiki_page_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {
        "slug": "imported-wiki-page",
        "content": "Imported wiki_page",
        "attachments": [{}],
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400
    assert len(response.data) == 1
    assert WikiPage.objects.filter(slug="imported-wiki-page").count() == 0


#######################################################
## tes api/v1/importer/wiki-link
#######################################################

def test_invalid_wiki_link_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-link", args=[project.pk])
    data = {}

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_valid_wiki_link_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("importer-wiki-link", args=[project.pk])
    data = {
        "title": "Imported wiki_link",
        "href": "imported-wiki-link",
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    response.data


##################################################################
## tes taiga.export_import.services.store_project_from_dict
##################################################################

def test_services_store_project_from_dict_with_no_projects_slots_available(client):
    user = f.UserFactory.create(max_private_projects=0)

    data = {
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True
    }

    with pytest.raises(TaigaImportError) as excinfo:
        project = services.store_project_from_dict(data, owner=user)

    assert "can't have more private projects" in str(excinfo.value)


def test_services_store_project_from_dict_with_no_members_private_project_slots_available(client):
    user = f.UserFactory.create(max_memberships_private_projects=2)

    data = {
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True,
        "roles": [{"name": "Role"}],
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            }
        ]
    }

    with pytest.raises(TaigaImportError) as excinfo:
        project = services.store_project_from_dict(data, owner=user)

    assert "reaches your current limit of memberships for private" in str(excinfo.value)


def test_services_store_project_from_dict_with_no_members_public_project_slots_available(client):
    user = f.UserFactory.create(max_memberships_public_projects=2)

    data = {
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False,
        "roles": [{"name": "Role"}],
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            }
        ]
    }

    with pytest.raises(TaigaImportError) as excinfo:
        project = services.store_project_from_dict(data, owner=user)

    assert "reaches your current limit of memberships for public" in str(excinfo.value)


def test_services_store_project_from_dict_with_issue_priorities_names_as_None(client):
    user = f.UserFactory.create()
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "issue_types": [{"name": "Bug"}],
        "issue_statuses": [{"name": "New"}],
        "priorities": [{"name": "None", "order": 5, "color": "#CC0000"}],
        "severities": [{"name": "Normal", "order": 5, "color": "#CC0000"}],
        "issues": [{
            "status": "New",
            "priority": "None",
            "severity": "Normal",
            "type": "Bug",
            "subject": "Test"}]}

    project = services.store_project_from_dict(data, owner=user)
    assert project.issues.first().priority.name == "None"


##################################################################
## tes api/v1/importer/load-dummp
##################################################################

def test_invalid_dump_import(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(b"test")
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400
    assert response.data["_error_message"] == "Invalid dump format"


def test_valid_dump_import_without_enough_public_projects_slots(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_public_projects=0)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "public-project-without-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400
    assert "can't have more public projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "False"
    assert Project.objects.filter(slug="public-project-without-slots").count() == 0


def test_valid_dump_import_without_enough_private_projects_slots(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_private_projects=0)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "private-project-without-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400
    assert "can't have more private projects" in response.data["_error_message"]
    assert response["Taiga-Info-Project-Memberships"] == "1"
    assert response["Taiga-Info-Project-Is-Private"] == "True"
    assert Project.objects.filter(slug="private-project-without-slots").count() == 0


def test_valid_dump_import_without_enough_membership_private_project_slots_one_project(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_memberships_private_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "project-without-memberships-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True,
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
            {
                "email": "test6@test.com",
                "role": "Role",
            },
        ],
        "roles": [{"name": "Role"}]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400
    assert "reaches your current limit of memberships for private" in response.data["_error_message"]
    assert Project.objects.filter(slug="project-without-memberships-slots").count() == 0


def test_valid_dump_import_without_enough_membership_public_project_slots_one_project(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_memberships_public_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "project-without-memberships-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False,
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
            {
                "email": "test6@test.com",
                "role": "Role",
            },
        ],
        "roles": [{"name": "Role"}]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400
    assert "reaches your current limit of memberships for public" in response.data["_error_message"]
    assert Project.objects.filter(slug="project-without-memberships-slots").count() == 0


def test_valid_dump_import_with_enough_membership_private_project_slots_multiple_projects(client, settings):
    settings.CELERY_ENABLED = False

    user = f.UserFactory.create(max_memberships_private_projects=10)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "project-without-memberships-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True,
        "roles": [{"name": "Role"}],
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
            {
                "email": "test6@test.com",
                "role": "Role",
            }
        ]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert "id" in response.data
    assert response.data["name"] == "Valid project"


def test_valid_dump_import_with_enough_membership_public_project_slots_multiple_projects(client, settings):
    settings.CELERY_ENABLED = False

    user = f.UserFactory.create(max_memberships_public_projects=10)
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    f.MembershipFactory.create(project=project)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "project-without-memberships-slots",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False,
        "roles": [{"name": "Role"}],
        "memberships": [
            {
                "email": "test1@test.com",
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
            {
                "email": "test6@test.com",
                "role": "Role",
            }
        ]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert "id" in response.data
    assert response.data["name"] == "Valid project"



def test_valid_dump_import_with_the_limit_of_membership_whit_you_for_private_project(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_memberships_private_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "private-project-with-memberships-limit-with-you",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True,
        "memberships": [
            {
                "email": user.email,
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
        ],
        "roles": [{"name": "Role"}]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert Project.objects.filter(slug="private-project-with-memberships-limit-with-you").count() == 1


def test_valid_dump_import_with_the_limit_of_membership_whit_you_for_public_project(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_memberships_public_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "public-project-with-memberships-limit-with-you",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False,
        "memberships": [
            {
                "email": user.email,
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
        ],
        "roles": [{"name": "Role"}]
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert Project.objects.filter(slug="public-project-with-memberships-limit-with-you").count() == 1


def test_valid_dump_import_with_celery_disabled(client, settings):
    settings.CELERY_ENABLED = False

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert "id" in response.data
    assert response.data["name"] == "Valid project"


def test_invalid_dump_import_with_celery_disabled(client, settings):
    settings.CELERY_ENABLED = False
    user = f.UserFactory.create(max_memberships_public_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "invalid-project",
        "name": "Invalid project",
        "description": "Valid project desc",
        "is_private": False,
        "memberships": [
            {
                "email": user.email,
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
        ],
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 400


def test_valid_dump_import_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 202
    assert "import_id" in response.data
    assert Project.objects.filter(slug="valid-project").count() == 1


def test_invalid_dump_import_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True
    user = f.UserFactory.create(max_memberships_public_projects=5)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "invalid-project",
        "name": "Invalid project",
        "description": "Valid project desc",
        "is_private": False,
        "memberships": [
            {
                "email": user.email,
                "role": "Role",
            },
            {
                "email": "test2@test.com",
                "role": "Role",
            },
            {
                "email": "test3@test.com",
                "role": "Role",
            },
            {
                "email": "test4@test.com",
                "role": "Role",
            },
            {
                "email": "test5@test.com",
                "role": "Role",
            },
        ],
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 202
    assert "import_id" in response.data
    assert Project.objects.filter(slug="invalid-project").count() == 0


def test_dump_import_throttling(client, settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["import-dump-mode"] = "1/minute"

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": project.slug,
        "name": "Test import",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    response = client.post(url, {'dump': data})
    assert response.status_code == 429


def test_valid_dump_import_without_slug(client):
    project = f.ProjectFactory.create(slug="existing-slug")
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "name": "Project name",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201


def test_valid_dump_import_with_logo(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": "valid-project",
        "name": "Valid project",
        "description": "Valid project desc",
        "is_private": False,
        "logo": {
            "name": "logo.bmp",
            "data": base64.b64encode(DUMMY_BMP_DATA).decode("utf-8")
        }
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert "id" in response.data
    assert response.data["name"] == "Valid project"
    assert "logo_small_url" in response.data
    assert response.data["logo_small_url"] != None
    assert "logo_big_url" in response.data
    assert response.data["logo_big_url"] != None


def test_valid_project_import_and_disabled_is_featured(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{
            "permissions": [],
            "name": "Test"
        }],
        "is_featured": True
    }

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data["owner"] == user.email
    assert response.data["is_featured"] == False


def test_dump_import_duplicated_project(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-load-dump")

    data = ContentFile(bytes(json.dumps({
        "slug": project.slug,
        "name": "Test import",
        "description": "Valid project desc",
        "is_private": True
    }), "utf-8"))
    data.name = "test"

    response = client.post(url, {'dump': data})
    assert response.status_code == 201
    assert response.data["name"] == "Test import"
    assert response.data["slug"] == "{}-test-import".format(user.username)
