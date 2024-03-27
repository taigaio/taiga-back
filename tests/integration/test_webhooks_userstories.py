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


from taiga.base.utils import json

def test_webhooks_when_create_user_story(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "create"
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id


def test_webhooks_when_update_user_story(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

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
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["data"]["subject"] == obj.subject
        assert data["change"]["comment"] == "test_comment"
        assert data["change"]["diff"]["subject"]["to"] == data["data"]["subject"]
        assert data["change"]["diff"]["subject"]["from"] !=  data["data"]["subject"]


def test_webhooks_when_update_assigned_users_user_story(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    user = f.create_user()
    obj.assigned_users.add(user)
    obj.save()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner,)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]

        assert data["action"] == "change"
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert len(data["data"]["assigned_users"]) == \
            obj.assigned_users.count()
        assert data["data"]["assigned_users"] == [user.id]
        assert not data["change"]["diff"]["assigned_users"]["from"]
        assert data["change"]["diff"]["assigned_users"]["to"] == user.username


def test_webhooks_when_delete_user_story(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, delete=True)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "delete"
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert "data" in data


def test_webhooks_when_update_user_story_attachments(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    # Create attachments
    attachment1 = f.UserStoryAttachmentFactory(project=obj.project, content_object=obj, owner=obj.owner)
    attachment2 = f.UserStoryAttachmentFactory(project=obj.project, content_object=obj, owner=obj.owner)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner, comment="test_comment")
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "userstory"
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
        assert data["type"] == "userstory"
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
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["attachments"]["new"]) == 0
        assert len(data["change"]["diff"]["attachments"]["changed"]) == 0
        assert len(data["change"]["diff"]["attachments"]["deleted"]) == 1


def test_webhooks_when_update_user_story_custom_attributes(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    obj = f.UserStoryFactory.create(project=project)

    custom_attr_1 = f.UserStoryCustomAttributeFactory(project=obj.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=obj.project)
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
        assert data["type"] == "userstory"
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
        assert data["type"] == "userstory"
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
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == "test_comment"
        assert len(data["change"]["diff"]["custom_attributes"]["new"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["changed"]) == 0
        assert len(data["change"]["diff"]["custom_attributes"]["deleted"]) == 1


def test_webhooks_when_update_user_story_points(settings):
    settings.WEBHOOKS_ENABLED = True
    project = f.ProjectFactory()
    f.WebhookFactory.create(project=project)
    f.WebhookFactory.create(project=project)

    role1 = f.RoleFactory.create(project=project)
    role2 = f.RoleFactory.create(project=project)

    points1 = f.PointsFactory.create(project=project, value=None)
    points2 = f.PointsFactory.create(project=project, value=1)
    points3 = f.PointsFactory.create(project=project, value=2)

    obj = f.UserStoryFactory.create(project=project)
    obj.role_points.all().delete()

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

    # Set points
    f.RolePointsFactory.create(user_story=obj, role=role1, points=points1)
    f.RolePointsFactory.create(user_story=obj, role=role2, points=points2)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == ""
        assert data["change"]["diff"]["points"][role1.name]["from"] == None
        assert data["change"]["diff"]["points"][role1.name]["to"] == points1.name
        assert data["change"]["diff"]["points"][role2.name]["from"] == None
        assert data["change"]["diff"]["points"][role2.name]["to"] == points2.name

    # Change points
    obj.role_points.all().update(points=points3)

    with patch('taiga.webhooks.tasks._send_request') as send_request_mock:
        services.take_snapshot(obj, user=obj.owner)
        assert send_request_mock.call_count == 2

        (webhook_id, url, key, data) = send_request_mock.call_args[0]
        assert data["action"] == "change"
        assert data["type"] == "userstory"
        assert data["by"]["id"] == obj.owner.id
        assert "date" in data
        assert data["data"]["id"] == obj.id
        assert data["change"]["comment"] == ""
        assert data["change"]["diff"]["points"][role1.name]["from"] == points1.name
        assert data["change"]["diff"]["points"][role1.name]["to"] == points3.name
        assert data["change"]["diff"]["points"][role2.name]["from"] == points2.name
        assert data["change"]["diff"]["points"][role2.name]["to"] == points3.name
