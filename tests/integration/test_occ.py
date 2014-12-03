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
from unittest.mock import patch

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.issues.models import Issue
from taiga.projects.wiki.models import WikiPage
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_valid_us_creation(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)

    client.login(user)

    url = reverse("userstories-list")
    data = {
        'project': project.id,
        'subject': 'test',
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201


def test_invalid_concurrent_save_for_issue(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("issues-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.IssueStatusFactory.create(project=project).id,
                      "severity": f.SeverityFactory.create(project=project).id,
                      "type": f.IssueTypeFactory.create(project=project).id,
                      "priority": f.PriorityFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.content

        issue_id = json.loads(response.content)["id"]
        url = reverse("issues-detail", args=(issue_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400


def test_valid_concurrent_save_for_issue_different_versions(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("issues-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.IssueStatusFactory.create(project=project).id,
                      "severity": f.SeverityFactory.create(project=project).id,
                      "type": f.IssueTypeFactory.create(project=project).id,
                      "priority": f.PriorityFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.content

        issue_id = json.loads(response.content)["id"]
        url = reverse("issues-detail", args=(issue_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":2, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_valid_concurrent_save_for_issue_different_fields(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("issues-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.IssueStatusFactory.create(project=project).id,
                      "severity": f.SeverityFactory.create(project=project).id,
                      "type": f.IssueTypeFactory.create(project=project).id,
                      "priority": f.PriorityFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.content

        issue_id = json.loads(response.content)["id"]
        url = reverse("issues-detail", args=(issue_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "description": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_invalid_concurrent_save_for_wiki_page(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.wiki.api.WikiViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("wiki-list")
        data = {"project": project.id, "slug": "test"}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.content

        wiki_id = json.loads(response.content)["id"]
        url = reverse("wiki-detail", args=(wiki_id,))
        data = {"version":1, "content": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "content": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400


def test_valid_concurrent_save_for_wiki_page_different_versions(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.wiki.api.WikiViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("wiki-list")
        data = {"project": project.id, "slug": "test"}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.content

        wiki_id = json.loads(response.content)["id"]
        url = reverse("wiki-detail", args=(wiki_id,))
        data = {"version":1, "content": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":2, "content": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_invalid_concurrent_save_for_us(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    userstory = f.UserStoryFactory.create(version=10, project=project)
    client.login(user)

    mock_path = "taiga.projects.userstories.api.UserStoryViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("userstories-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.UserStoryStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        userstory_id = json.loads(response.content)["id"]
        url = reverse("userstories-detail", args=(userstory_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400


def test_valid_concurrent_save_for_us_different_versions(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.userstories.api.UserStoryViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("userstories-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.UserStoryStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        userstory_id = json.loads(response.content)["id"]
        url = reverse("userstories-detail", args=(userstory_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":2, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_valid_concurrent_save_for_us_different_fields(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.userstories.api.UserStoryViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("userstories-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.UserStoryStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        userstory_id = json.loads(response.content)["id"]
        url = reverse("userstories-detail", args=(userstory_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "description": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_invalid_concurrent_save_for_task(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("tasks-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.TaskStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        task_id = json.loads(response.content)["id"]
        url = reverse("tasks-detail", args=(task_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400


def test_valid_concurrent_save_for_task_different_versions(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("tasks-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.TaskStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        task_id = json.loads(response.content)["id"]
        url = reverse("tasks-detail", args=(task_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":2, "subject": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200


def test_valid_concurrent_save_for_task_different_fields(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user, is_owner=True)
    client.login(user)

    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("tasks-list")
        data = {"subject": "test",
                      "project": project.id,
                      "status": f.TaskStatusFactory.create(project=project).id}
        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201

        task_id = json.loads(response.content)["id"]
        url = reverse("tasks-detail", args=(task_id,))
        data = {"version":1, "subject": "test 1"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200

        data = {"version":1, "description": "test 2"}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 200
