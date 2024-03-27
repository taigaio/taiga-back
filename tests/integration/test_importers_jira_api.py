# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
import json

from unittest import mock

from django.urls import reverse

from .. import factories as f
from taiga.base.utils import json
from taiga.base import exceptions as exc
from taiga.users.models import AuthData


pytestmark = pytest.mark.django_db


fake_token = "access.secret"


def test_auth_url(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-auth-url")+"?url=http://jiraserver"

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporter:
        JiraNormalImporter.get_auth_url.return_value = ("test_oauth_token", "test_oauth_secret", "http://jira-server-url")
        response = client.get(url, content_type="application/json")

    auth_data = user.auth_data.get(key="jira-oauth")
    assert auth_data.extra['oauth_token'] == "test_oauth_token"
    assert auth_data.extra['oauth_secret'] == "test_oauth_secret"
    assert auth_data.extra['url'] == "http://jiraserver"

    assert response.status_code == 200
    assert 'url' in response.data
    assert response.data['url'] == "http://jira-server-url"


def test_authorize(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-auth-url")
    authorize_url = reverse("importers-jira-authorize")

    AuthData.objects.get_or_create(
        user=user,
        key="jira-oauth",
        value="",
        extra={
            "oauth_token": "test-oauth-token",
            "oauth_secret": "test-oauth-secret",
            "url": "http://jiraserver",
        }
    )

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporter:
        JiraNormalImporter.get_access_token.return_value = {
            "access_token": "test-access-token",
            "access_token_secret": "test-access-token-secret"
        }
        response = client.post(authorize_url, content_type="application/json", data={})

    assert response.status_code == 200
    assert 'token' in response.data
    assert response.data['token'] == "test-access-token.test-access-token-secret"
    assert 'url' in response.data
    assert response.data['url'] == "http://jiraserver"


def test_authorize_without_token_and_secret(client):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-jira-authorize")
    AuthData.objects.filter(user=user, key="jira-oauth").delete()

    response = client.post(authorize_url, content_type="application/json", data={})

    assert response.status_code == 400
    assert 'token' not in response.data


def test_import_jira_list_users(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-list-users")

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "fullName": "user1", "email": None},
            {"id": 2, "fullName": "user2", "email": None}
        ]
        JiraNormalImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver", "project": 1}))

    assert response.status_code == 200
    assert response.data[0]["id"] == 1
    assert response.data[1]["id"] == 2


def test_import_jira_list_users_without_project(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-list-users")

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "fullName": "user1", "email": None},
            {"id": 2, "fullName": "user2", "email": None}
        ]
        JiraNormalImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver"}))

    assert response.status_code == 400


def test_import_jira_list_users_with_problem_on_request(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-list-users")

    with mock.patch('taiga.importers.jira.common.JiraClient') as JiraClientMock:
        instance = mock.Mock()
        instance.get.side_effect = exc.WrongArguments("Invalid Request")
        JiraClientMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver", "project": 1}))

    assert response.status_code == 400


def test_import_jira_list_projects(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-list-projects")

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporterMock:
        with mock.patch('taiga.importers.jira.api.JiraAgileImporter') as JiraAgileImporterMock:
            instance = mock.Mock()
            instance.list_projects.return_value = [{"name": "project1"}, {"name": "project2"}]
            JiraNormalImporterMock.return_value = instance
            instance_agile = mock.Mock()
            instance_agile.list_projects.return_value = [{"name": "agile1"}, {"name": "agile2"}]
            JiraAgileImporterMock.return_value = instance_agile
            response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver"}))

    assert response.status_code == 200
    assert response.data[0] == {"name": "agile1"}
    assert response.data[1] == {"name": "agile2"}
    assert response.data[2] == {"name": "project1"}
    assert response.data[3] == {"name": "project2"}


def test_import_jira_list_projects_with_problem_on_request(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-list-projects")

    with mock.patch('taiga.importers.jira.common.JiraClient') as JiraClientMock:
        instance = mock.Mock()
        instance.get.side_effect = exc.WrongArguments("Invalid Request")
        JiraClientMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver"}))

    assert response.status_code == 400


def test_import_jira_project_without_project_id(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-import-project")

    with mock.patch('taiga.importers.jira.tasks.JiraNormalImporter') as JiraNormalImporterMock:
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver"}))

    assert response.status_code == 400
    settings.CELERY_ENABLED = False


def test_import_jira_project_without_url(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-jira-import-project")

    with mock.patch('taiga.importers.jira.tasks.JiraNormalImporter') as JiraNormalImporterMock:
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "project_id": 1}))

    assert response.status_code == 400
    settings.CELERY_ENABLED = False


def test_import_jira_project_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="async-imported-project")
    client.login(user)

    url = reverse("importers-jira-import-project")

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as ApiJiraNormalImporterMock:
        with mock.patch('taiga.importers.jira.tasks.JiraNormalImporter') as TasksJiraNormalImporterMock:
            TasksJiraNormalImporterMock.return_value.import_project.return_value = project
            ApiJiraNormalImporterMock.return_value.list_issue_types.return_value = []
            response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver", "project": 1}))

    assert response.status_code == 202
    assert "task_id" in response.data
    settings.CELERY_ENABLED = False


def test_import_jira_project_with_celery_disabled(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="imported-project")
    client.login(user)

    url = reverse("importers-jira-import-project")

    with mock.patch('taiga.importers.jira.api.JiraNormalImporter') as JiraNormalImporterMock:
        instance = mock.Mock()
        instance.import_project.return_value = project
        instance.list_issue_types.return_value = []
        JiraNormalImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "access.secret", "url": "http://jiraserver", "project": 1}))

    assert response.status_code == 200
    assert "slug" in response.data
    assert response.data['slug'] == "imported-project"
