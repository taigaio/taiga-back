# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from unittest import mock

from django.urls import reverse

from .. import factories as f
from taiga.base.utils import json


pytestmark = pytest.mark.django_db


def test_invalid_project_export(client):
    user = f.UserFactory.create()
    client.login(user)

    url = reverse("exporter-detail", args=[1000000])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 404


def test_valid_project_export_with_celery_disabled(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response_data = response.data
    assert "url" in response_data
    assert response_data["url"].endswith(".json")


def test_valid_project_export_with_celery_disabled_and_gzip(client, settings):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url+"?dump_format=gzip", content_type="application/json")
    assert response.status_code == 200
    response_data = response.data
    assert "url" in response_data
    assert response_data["url"].endswith(".gz")


def test_valid_project_export_with_celery_enabled(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    #delete_project_dump task should have been launched
    with mock.patch('taiga.export_import.tasks.delete_project_dump') as delete_project_dump_mock:
        response = client.get(url, content_type="application/json")
        assert response.status_code == 202
        response_data = response.data
        assert "export_id" in response_data

        args = (project.id, project.slug, response_data["export_id"], "plain")
        kwargs = {"countdown": settings.EXPORTS_TTL}
        delete_project_dump_mock.apply_async.assert_called_once_with(args, **kwargs)
    settings.CELERY_ENABLED = False


def test_valid_project_export_with_celery_enabled_and_gzip(client, settings):
    settings.CELERY_ENABLED = True

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    #delete_project_dump task should have been launched
    with mock.patch('taiga.export_import.tasks.delete_project_dump') as delete_project_dump_mock:
        response = client.get(url+"?dump_format=gzip", content_type="application/json")
        assert response.status_code == 202
        response_data = response.data
        assert "export_id" in response_data

        args = (project.id, project.slug, response_data["export_id"], "gzip")
        kwargs = {"countdown": settings.EXPORTS_TTL}
        delete_project_dump_mock.apply_async.assert_called_once_with(args, **kwargs)
    settings.CELERY_ENABLED = False


def test_valid_project_with_throttling(client, settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["import-dump-mode"] = "1/minute"

    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory(project=project, user=user, is_admin=True)
    client.login(user)

    url = reverse("exporter-detail", args=[project.pk])

    response = client.get(url, content_type="application/json")
    assert response.status_code == 200
    response = client.get(url, content_type="application/json")
    assert response.status_code == 429
