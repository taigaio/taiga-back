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
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner)
            assert session_send_mock.call_count == 0

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
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
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 2

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 2

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner)
            assert session_send_mock.call_count == 0

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
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
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert session_send_mock.call_count == 1

    for obj in objects:
        with patch("taiga.webhooks.tasks.requests.Session.send", return_value=response) as session_send_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert session_send_mock.call_count == 1
