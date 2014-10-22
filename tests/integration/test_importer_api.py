# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
import json
import base64
import datetime

from django.core.urlresolvers import reverse

from .. import factories as f

from taiga.projects.models import Project
from taiga.projects.issues.models import Issue
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task
from taiga.projects.wiki.models import WikiPage

from taiga.export_import.service import project_to_dict
from taiga.export_import.dump_service import dict_to_project

pytestmark = pytest.mark.django_db


def test_invalid_project_import(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_project_import_without_extra_data(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    must_empty_children = [
        "issues", "user_stories", "roles", "us_statuses", "wiki_pages", "priorities",
        "severities", "milestones", "points", "issue_types", "task_statuses",
        "memberships", "issue_statuses", "wiki_links",
    ]

    assert all(map(lambda x: len(response_data[x]) == 0, must_empty_children))
    assert response_data["owner"] == user.email

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

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    # The new membership and the owner membership
    assert len(response_data["memberships"]) == 2

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

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    must_empty_children = [
        "issues", "user_stories", "wiki_pages", "milestones",
        "wiki_links",
    ]

    must_one_instance_children = [
        "roles", "us_statuses", "severities", "priorities", "points",
        "issue_types", "task_statuses", "issue_statuses", "memberships",
    ]

    assert all(map(lambda x: len(response_data[x]) == 0, must_empty_children))
    # Allwais is created at least the owner membership
    assert all(map(lambda x: len(response_data[x]) == 1, must_one_instance_children))
    assert response_data["owner"] == user.email

def test_invalid_project_import_with_extra_data(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importer-list")
    data = {
        "name": "Imported project",
        "description": "Imported project",
        "roles": [{ }],
        "us_statuses": [{ }],
        "severities": [{ }],
        "priorities": [{ }],
        "points": [{ }],
        "issue_types": [{ }],
        "task_statuses": [{ }],
        "issue_statuses": [{ }],
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 8
    assert Project.objects.filter(slug="imported-project").count() == 0

def test_invalid_issue_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-issue", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_user_story_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "finish_date": "2014-10-24T00:00:00+0000"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["subject"] == "Imported issue"
    assert response_data["finish_date"] == "2014-10-24T00:00:00+0000"


def test_valid_issue_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None

def test_valid_issue_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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
        }]
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["attachments"]) == 1
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None
    assert response_data["finished_date"] == "2014-10-24T00:00:00+0000"

def test_invalid_issue_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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
        "attachments": [{ }],
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1
    assert Issue.objects.filter(subject="Imported issue").count() == 0

def test_invalid_issue_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "priority": "Not valid"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "severity": "Not valid"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

    url = reverse("importer-issue", args=[project.pk])
    data = {
        "subject": "Imported issue",
        "description": "Imported issue",
        "type": "Not valid"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

def test_invalid_us_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_us_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Test"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None

def test_valid_us_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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
        }]
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["attachments"]) == 1
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None

def test_invalid_us_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported us",
        "description": "Imported us",
        "attachments": [{ }],
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1
    assert UserStory.objects.filter(subject="Imported us").count() == 0

def test_invalid_us_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_us_status = f.UserStoryStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-us", args=[project.pk])
    data = {
        "subject": "Imported us",
        "description": "Imported us",
        "status": "Not valid"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

def test_invalid_task_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_task_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Test"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None

def test_valid_task_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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
        }]
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["attachments"]) == 1
    assert response_data["owner"] == user.email
    assert response_data["ref"] is not None

def test_invalid_task_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "attachments": [{ }],
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1
    assert Task.objects.filter(subject="Imported task").count() == 0

def test_invalid_task_import_with_bad_choices(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    project.default_task_status = f.TaskStatusFactory.create(project=project)
    project.save()
    client.login(user)

    url = reverse("importer-task", args=[project.pk])
    data = {
        "subject": "Imported task",
        "description": "Imported task",
        "status": "Not valid"
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1

def test_valid_task_with_user_story(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    assert us.tasks.all().count() == 1

def test_invalid_wiki_page_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_wiki_page_import_without_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {
        "slug": "imported-wiki-page",
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["owner"] == user.email

def test_valid_wiki_page_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
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
        }]
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data["attachments"]) == 1
    assert response_data["owner"] == user.email

def test_invalid_wiki_page_import_with_extra_data(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-wiki-page", args=[project.pk])
    data = {
        "slug": "imported-wiki-page",
        "content": "Imported wiki_page",
        "attachments": [{ }],
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert len(response_data) == 1
    assert WikiPage.objects.filter(slug="imported-wiki-page").count() == 0

def test_invalid_wiki_link_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-wiki-link", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_wiki_link_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-wiki-link", args=[project.pk])
    data = {
        "title": "Imported wiki_link",
        "href": "imported-wiki-link",
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))

def test_invalid_milestone_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {}

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_milestone_import(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {
        "name": "Imported milestone",
        "estimated_start": "2014-10-10",
        "estimated_finish": "2014-10-20",
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201
    response_data = json.loads(response.content.decode("utf-8"))

def test_milestone_import_duplicated_milestone(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    client.login(user)

    url = reverse("importer-milestone", args=[project.pk])
    data = {
        "name": "Imported milestone",
        "estimated_start": "2014-10-10",
        "estimated_finish": "2014-10-20",
    }
    # We create twice the same milestone
    response = client.post(url, json.dumps(data), content_type="application/json")
    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400
    response_data = json.loads(response.content.decode("utf-8"))
    assert response_data["milestones"][0]["name"][0] == "Name duplicated for the project"
