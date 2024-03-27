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
from taiga.importers import exceptions
from taiga.base.utils import json
from taiga.base import exceptions as exc


pytestmark = pytest.mark.django_db


def test_auth_url(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-auth-url")+"?uri=http://localhost:9001/project/new?from=github"

    response = client.get(url, content_type="application/json")

    assert response.status_code == 200
    assert 'url' in response.data
    assert response.data['url'] == "https://github.com/login/oauth/authorize?client_id=&scope=user,repo&redirect_uri=http://localhost:9001/project/new?from=github"

def test_authorize(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-github-authorize")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        GithubImporterMock.get_access_token.return_value = "token"
        response = client.post(authorize_url, content_type="application/json", data=json.dumps({"code": "code"}))
        assert GithubImporterMock.get_access_token.calledWith(
            settings.IMPORTERS['github']['client_id'],
            settings.IMPORTERS['github']['client_secret'],
            "code"
        )

    assert response.status_code == 200
    assert 'token' in response.data
    assert response.data['token'] == "token"

def test_authorize_without_code(client):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-github-authorize")

    response = client.post(authorize_url, content_type="application/json", data=json.dumps({}))

    assert response.status_code == 400
    assert 'token' not in response.data
    assert '_error_message' in response.data
    assert response.data['_error_message'] == "Code param needed"


def test_authorize_with_bad_verify(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-github-authorize")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        GithubImporterMock.get_access_token.side_effect = exceptions.InvalidAuthResult()
        response = client.post(authorize_url, content_type="application/json", data=json.dumps({"code": "bad"}))
        assert GithubImporterMock.get_access_token.calledWith(
            settings.IMPORTERS['github']['client_id'],
            settings.IMPORTERS['github']['client_secret'],
            "bad"
        )

    assert response.status_code == 400
    assert 'token' not in response.data
    assert '_error_message' in response.data
    assert response.data['_error_message'] == "Invalid auth data"


def test_import_github_list_users(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-list-users")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "username": "user1", "full_name": "user1", "detected_user": None},
            {"id": 2, "username": "user2", "full_name": "user2", "detected_user": None}
        ]
        GithubImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 200
    assert response.data[0]["id"] == 1
    assert response.data[1]["id"] == 2


def test_import_github_list_users_without_project(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-list-users")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "username": "user1", "full_name": "user1", "detected_user": None},
            {"id": 2, "username": "user2", "full_name": "user2", "detected_user": None}
        ]
        GithubImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400


def test_import_github_list_users_with_problem_on_request(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-list-users")

    with mock.patch('taiga.importers.github.importer.GithubClient') as GithubClientMock:
        instance = mock.Mock()
        instance.get.side_effect = exc.WrongArguments("Invalid Request")
        GithubClientMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 400


def test_import_github_list_projects(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-list-projects")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        instance = mock.Mock()
        instance.list_projects.return_value = ["project1", "project2"]
        GithubImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 200
    assert response.data[0] == "project1"
    assert response.data[1] == "project2"


def test_import_github_list_projects_with_problem_on_request(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-list-projects")

    with mock.patch('taiga.importers.github.importer.GithubClient') as GithubClientMock:
        instance = mock.Mock()
        instance.get.side_effect = exc.WrongArguments("Invalid Request")
        GithubClientMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400


def test_import_github_project_without_project_id(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-github-import-project")

    with mock.patch('taiga.importers.github.tasks.GithubImporter') as GithubImporterMock:
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400
    settings.CELERY_ENABLED = False


def test_import_github_project_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="async-imported-project")
    client.login(user)

    url = reverse("importers-github-import-project")

    with mock.patch('taiga.importers.github.tasks.GithubImporter') as GithubImporterMock:
        instance = mock.Mock()
        instance.import_project.return_value = project
        GithubImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 202
    assert "task_id" in response.data
    settings.CELERY_ENABLED = False


def test_import_github_project_with_celery_disabled(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="imported-project")
    client.login(user)

    url = reverse("importers-github-import-project")

    with mock.patch('taiga.importers.github.api.GithubImporter') as GithubImporterMock:
        instance = mock.Mock()
        instance.import_project.return_value = project
        GithubImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 200
    assert "slug" in response.data
    assert response.data['slug'] == "imported-project"
