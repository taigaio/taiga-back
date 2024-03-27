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


def test_auth_url(client, settings):
    user = f.UserFactory.create()
    client.login(user)
    settings.IMPORTERS['asana']['callback_url'] = "http://testserver/url"
    settings.IMPORTERS['asana']['app_id'] = "test-id"
    settings.IMPORTERS['asana']['app_secret'] = "test-secret"

    url = reverse("importers-asana-auth-url")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        AsanaImporterMock.get_auth_url.return_value = "https://auth_url"
        response = client.get(url, content_type="application/json")
        assert AsanaImporterMock.get_auth_url.calledWith(
            settings.IMPORTERS['asana']['app_id'],
            settings.IMPORTERS['asana']['app_secret'],
            settings.IMPORTERS['asana']['callback_url']
        )

    assert response.status_code == 200
    assert 'url' in response.data
    assert response.data['url'] == "https://auth_url"


def test_authorize(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-asana-authorize")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        AsanaImporterMock.get_access_token.return_value = "token"
        response = client.post(authorize_url, content_type="application/json", data=json.dumps({"code": "code"}))
        assert AsanaImporterMock.get_access_token.calledWith(
            settings.IMPORTERS['asana']['app_id'],
            settings.IMPORTERS['asana']['app_secret'],
            "code"
        )

    assert response.status_code == 200
    assert 'token' in response.data
    assert response.data['token'] == "token"


def test_authorize_without_code(client):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-asana-authorize")

    response = client.post(authorize_url, content_type="application/json", data=json.dumps({}))

    assert response.status_code == 400
    assert 'token' not in response.data
    assert '_error_message' in response.data
    assert response.data['_error_message'] == "Code param needed"


def test_authorize_with_bad_verify(client, settings):
    user = f.UserFactory.create()
    client.login(user)

    authorize_url = reverse("importers-asana-authorize")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        AsanaImporterMock.get_access_token.side_effect = exceptions.InvalidRequest()
        response = client.post(authorize_url, content_type="application/json", data=json.dumps({"code": "bad"}))
        assert AsanaImporterMock.get_access_token.calledWith(
            settings.IMPORTERS['asana']['app_id'],
            settings.IMPORTERS['asana']['app_secret'],
            "bad"
        )

    assert response.status_code == 400
    assert 'token' not in response.data
    assert '_error_message' in response.data
    assert response.data['_error_message'] == "Invalid Asana API request"


def test_import_asana_list_users(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-list-users")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "username": "user1", "full_name": "user1", "detected_user": None},
            {"id": 2, "username": "user2", "full_name": "user2", "detected_user": None}
        ]
        AsanaImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 200
    assert response.data[0]["id"] == 1
    assert response.data[1]["id"] == 2


def test_import_asana_list_users_without_project(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-list-users")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        instance = mock.Mock()
        instance.list_users.return_value = [
            {"id": 1, "username": "user1", "full_name": "user1", "detected_user": None},
            {"id": 2, "username": "user2", "full_name": "user2", "detected_user": None}
        ]
        AsanaImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400


def test_import_asana_list_users_with_problem_on_request(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-list-users")

    with mock.patch('taiga.importers.asana.importer.AsanaClient') as AsanaClientMock:
        instance = mock.Mock()
        instance.workspaces.find_all.side_effect = exceptions.InvalidRequest()
        AsanaClientMock.oauth.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 400


def test_import_asana_list_projects(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-list-projects")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        instance = mock.Mock()
        instance.list_projects.return_value = ["project1", "project2"]
        AsanaImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 200
    assert response.data[0] == "project1"
    assert response.data[1] == "project2"


def test_import_asana_list_projects_with_problem_on_request(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-list-projects")

    with mock.patch('taiga.importers.asana.importer.AsanaClient') as AsanaClientMock:
        instance = mock.Mock()
        instance.workspaces.find_all.side_effect = exc.WrongArguments("Invalid Request")
        AsanaClientMock.oauth.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400


def test_import_asana_project_without_project_id(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    client.login(user)

    url = reverse("importers-asana-import-project")

    with mock.patch('taiga.importers.asana.tasks.AsanaImporter') as AsanaImporterMock:
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token"}))

    assert response.status_code == 400
    settings.CELERY_ENABLED = False


def test_import_asana_project_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="async-imported-project")
    client.login(user)

    url = reverse("importers-asana-import-project")

    with mock.patch('taiga.importers.asana.tasks.AsanaImporter') as AsanaImporterMock:
        instance = mock.Mock()
        instance.import_project.return_value = project
        AsanaImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 202
    assert "task_id" in response.data
    settings.CELERY_ENABLED = False


def test_import_asana_project_with_celery_disabled(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(slug="imported-project")
    client.login(user)

    url = reverse("importers-asana-import-project")

    with mock.patch('taiga.importers.asana.api.AsanaImporter') as AsanaImporterMock:
        instance = mock.Mock()
        instance.import_project.return_value = project
        AsanaImporterMock.return_value = instance
        response = client.post(url, content_type="application/json", data=json.dumps({"token": "token", "project": 1}))

    assert response.status_code == 200
    assert "slug" in response.data
    assert response.data['slug'] == "imported-project"
