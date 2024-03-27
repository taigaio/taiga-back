# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
from unittest.mock import patch
from unittest.mock import Mock

from .. import factories as f

from taiga.projects.history import services

pytestmark = pytest.mark.django_db(transaction=True)


def test_new_object_with_one_webhook_signal(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)

    objects = [
        f.IssueFactory.create(project=project),
        f.TaskFactory.create(project=project),
        f.UserStoryFactory.create(project=project),
        f.WikiPageFactory.create(project=project)
    ]

    response = Mock(status_code=200, headers={}, text="ok")
    response.elapsed.total_seconds.return_value = 100

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner)
            assert session_send_mock.call_count == 0

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert session_send_mock.call_count == 1


def test_new_object_with_two_webhook_signals(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    objects = [
        f.IssueFactory.create(project=project),
        f.TaskFactory.create(project=project),
        f.UserStoryFactory.create(project=project),
        f.WikiPageFactory.create(project=project)
    ]

    response = Mock(status_code=200, headers={}, text="ok")
    response.elapsed.total_seconds.return_value = 100

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 2

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 2

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner)
            assert session_send_mock.call_count == 0

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert session_send_mock.call_count == 2


def test_send_request_one_webhook_signal(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)

    objects = [
        f.IssueFactory.create(project=project),
        f.TaskFactory.create(project=project),
        f.UserStoryFactory.create(project=project),
        f.WikiPageFactory.create(project=project)
    ]

    response = Mock(status_code=200, headers={}, text="ok")
    response.elapsed.total_seconds.return_value = 100

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock, \
         patch("taiga.base.utils.urls.validate_private_url", return_value=True):
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert session_send_mock.call_count == 1
