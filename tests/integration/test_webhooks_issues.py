# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest
from unittest.mock import patch

from .. import factories as f

from taiga.projects.history import services


pytestmark = pytest.mark.django_db(transaction=True)


def test_webhooks_when_create_issue(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.IssueFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "create"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id


def test_webhooks_when_update_issue(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.IssueFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    obj.subject = "test webhook update"
    obj.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["data"]["subject"] == obj.subject
        assert data["change"]["comment"] == "test_comment"
        assert data["change"]["diff"]["subject"]["to"] == data["data"]["subject"]
        assert data["change"]["diff"]["subject"]["from"] != data["data"]["subject"]


def test_webhooks_when_delete_issue(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.IssueFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, delete=True)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "delete"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert "data" in data


def test_webhooks_when_update_issue_attachments(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.IssueFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    # Create attachments
    attachment1 = f.IssueAttachmentFactory(project=obj.project, content_object=obj, owner=obj.owner)
    attachment2 = f.IssueAttachmentFactory(project=obj.project, content_object=obj, owner=obj.owner)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["attachments"]["new"]) == 2
        assert len(data["change"]["diff"]["attachments"]["changed"]) == 0
        assert len(data["change"]["diff"]["attachments"]["deleted"]) == 0

    # Update attachment
    attachment1.description = "new attachment description"
    attachment1.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["attachments"]["new"]) == 0
        assert len(data["change"]["diff"]["attachments"]["changed"]) == 1
        assert len(data["change"]["diff"]["attachments"]["deleted"]) == 0

    # Delete attachment
    attachment2.delete()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["attachments"]["new"]) == 0
        assert len(data["change"]["diff"]["attachments"]["changed"]) == 0
        assert len(data["change"]["diff"]["attachments"]["deleted"]) == 1


def test_webhooks_when_update_issue_custom_attributes(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.IssueFactory.create(project=project)

    custom_attr_1 = f.IssueCustomAttributeFactory(project=obj.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.IssueCustomAttributeFactory(project=obj.project)
    ct2_id = "{}".format(custom_attr_2.id)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    # Create custom attributes
    obj.custom_attributes_values.attributes_values = {
        ct1_id: "test_1_updated",
        ct2_id: "test_2_updated"
    }
    obj.custom_attributes_values.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["custom_attributes"]["new"]) == 2
        assert len(data["change"]["diff"]["custom_attributes"]["changed"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["deleted"]) == 0

    # Update custom attributes
    obj.custom_attributes_values.attributes_values[ct1_id] = "test_2_updated"
    obj.custom_attributes_values.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["custom_attributes"]["new"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["changed"]) == 1
        assert len(data["change"]["diff"]["custom_attributes"]["deleted"]) == 0

    # Delete custom attributes
    del obj.custom_attributes_values.attributes_values[ct1_id]
    obj.custom_attributes_values.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "issue"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["custom_attributes"]["new"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["changed"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["deleted"]) == 1
