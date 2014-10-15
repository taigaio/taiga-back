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


def test_invalid_concurrent_save_for_issue(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    issue = f.IssueFactory.create(version=10, project=project)

    client.login(user)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("issues-detail", args=(issue.id,))
        data = {}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400

def test_valid_concurrent_save_for_issue(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    issue = f.IssueFactory.create(version=10, project=project)

    client.login(user)

    mock_path = "taiga.projects.issues.api.IssueViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("issues-detail", args=(issue.id,))
        data = {"version": 10}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert json.loads(response.content)['version'] == 11
        assert response.status_code == 200
        issue = Issue.objects.get(id=issue.id)
        assert issue.version == 11

def test_invalid_concurrent_save_for_wiki_page(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    wiki_page = f.WikiPageFactory.create(version=10, project=project, owner=user)
    client.login(user)

    url = reverse("wiki-detail", args=(wiki_page.id,))
    data = {}
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_concurrent_save_for_wiki_page(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    wiki_page = f.WikiPageFactory.create(version=10, project=project, owner=user)
    client.login(user)

    url = reverse("wiki-detail", args=(wiki_page.id,))
    data = {"version": 10}
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert json.loads(response.content)['version'] == 11
    assert response.status_code == 200
    wiki_page = WikiPage.objects.get(id=wiki_page.id)
    assert wiki_page.version == 11

def test_invalid_concurrent_save_for_us(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    userstory = f.UserStoryFactory.create(version=10, project=project)
    client.login(user)

    url = reverse("userstories-detail", args=(userstory.id,))
    data = {}
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 400

def test_valid_us_creation(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)

    client.login(user)

    url = reverse("userstories-list")
    data = {
        'project': project.id,
        'subject': 'test',
    }

    response = client.post(url, json.dumps(data), content_type="application/json")
    assert response.status_code == 201

def test_valid_concurrent_save_for_us(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    userstory = f.UserStoryFactory.create(version=10, project=project)
    client.login(user)

    url = reverse("userstories-detail", args=(userstory.id,))
    data = {"version": 10}
    response = client.patch(url, json.dumps(data), content_type="application/json")
    assert json.loads(response.content)['version'] == 11
    assert response.status_code == 200
    userstory = UserStory.objects.get(id=userstory.id)
    assert userstory.version == 11

def test_invalid_concurrent_save_for_task(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    task = f.TaskFactory.create(version=10, project=project)
    client.login(user)

    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("tasks-detail", args=(task.id,))
        data = {}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert response.status_code == 400

def test_valid_concurrent_save_for_task(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    membership = f.MembershipFactory.create(project=project, user=user)
    task = f.TaskFactory.create(version=10, project=project)
    client.login(user)

    mock_path = "taiga.projects.tasks.api.TaskViewSet.pre_conditions_on_save"
    with patch(mock_path) as m:
        url = reverse("tasks-detail", args=(task.id,))
        data = {"version": 10}
        response = client.patch(url, json.dumps(data), content_type="application/json")
        assert json.loads(response.content)['version'] == 11
        assert response.status_code == 200
        task = Task.objects.get(id=task.id)
        assert task.version == 11
