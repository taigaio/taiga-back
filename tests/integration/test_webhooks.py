# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Anler Hernández <hello@anler.me>
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

from .. import factories as f

from taiga.projects.history import services

pytestmark = pytest.mark.django_db


def test_new_object_with_one_webhook(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)

    objects = [
        f.IssueFactory.create(project=project),
        f.TaskFactory.create(project=project),
        f.UserStoryFactory.create(project=project),
        f.WikiPageFactory.create(project=project)
    ]

    for obj in objects:
        with patch('taiga.webhooks.tasks.create_webhook') as create_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert create_webhook_mock.call_count == 1

    for obj in objects:
        with patch('taiga.webhooks.tasks.change_webhook') as change_webhook_mock:
            services.take_snapshot(obj, user=obj.owner)
            assert change_webhook_mock.call_count == 0

    for obj in objects:
        with patch('taiga.webhooks.tasks.change_webhook') as change_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert change_webhook_mock.call_count == 1

    for obj in objects:
        with patch('taiga.webhooks.tasks.delete_webhook') as delete_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert delete_webhook_mock.call_count == 1


def test_new_object_with_two_webhook(settings):
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

    for obj in objects:
        with patch('taiga.webhooks.tasks.create_webhook') as create_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert create_webhook_mock.call_count == 2

    for obj in objects:
        with patch('taiga.webhooks.tasks.change_webhook') as change_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert change_webhook_mock.call_count == 2

    for obj in objects:
        with patch('taiga.webhooks.tasks.change_webhook') as change_webhook_mock:
            services.take_snapshot(obj, user=obj.owner)
            assert change_webhook_mock.call_count == 0

    for obj in objects:
        with patch('taiga.webhooks.tasks.delete_webhook') as delete_webhook_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert delete_webhook_mock.call_count == 2


def test_send_request_one_webhook(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)

    objects = [
        f.IssueFactory.create(project=project),
        f.TaskFactory.create(project=project),
        f.UserStoryFactory.create(project=project),
        f.WikiPageFactory.create(project=project)
    ]

    for obj in objects:
        with patch('taiga.webhooks.tasks._send_request') as _send_request_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test")
            assert _send_request_mock.call_count == 1

    for obj in objects:
        with patch('taiga.webhooks.tasks._send_request') as _send_request_mock:
            services.take_snapshot(obj, user=obj.owner, comment="test", delete=True)
            assert _send_request_mock.call_count == 1
