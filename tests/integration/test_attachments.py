# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from taiga.base.utils import json

from .. import factories as f

pytestmark = pytest.mark.django_db


def test_create_user_story_attachment_without_file(client):
    """
    Bug test "Don't create attachments without attached_file"
    """
    us = f.UserStoryFactory.create()
    f.MembershipFactory(project=us.project, user=us.owner, is_admin=True)
    attachment_data = {
        "description": "test",
        "project": us.project_id,
    }

    url = reverse('userstory-attachments-list')

    client.login(us.owner)
    response = client.post(url, attachment_data)
    assert response.status_code == 400


def test_create_attachment_on_wrong_project(client):
    issue1 = f.create_issue()
    issue2 = f.create_issue(owner=issue1.owner)
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_admin=True)

    assert issue1.owner == issue2.owner
    assert issue1.project.owner == issue2.project.owner

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue2.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile("test.txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.status_code == 400


def test_create_attachment_with_long_file_name(client):
    issue1 = f.create_issue()
    f.MembershipFactory(project=issue1.project, user=issue1.owner, is_admin=True)

    url = reverse("issue-attachments-list")

    data = {"description": "test",
            "object_id": issue1.pk,
            "project": issue1.project.id,
            "attached_file": SimpleUploadedFile(500*"x"+".txt", b"test")}

    client.login(issue1.owner)
    response = client.post(url, data)
    assert response.data["attached_file"].endswith("/"+100*"x"+".txt")


######################################
# Sorting attachments
######################################

def test_api_update_orders_in_bulk_succeeds_moved_to_the_begining(client):
    #
    # -------- |                     | --------
    #   att1   |   MOVE: att2, att3  |   att2
    #   att2   |   AFTER: bigining   |   att3
    #   att3   |                     |   att1
    #

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us = f.create_userstory(project=project)

    att1 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=1)
    att2 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=2)
    att3 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=3)

    url = reverse("userstory-attachments-bulk-update-order")

    data = {
        "object_id": us.id,
        "after_attachment_id": None,
        "bulk_attachments": [att2.id,
                             att3.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        att2.id,
        att3.id,
        att1.id,
    ]
    res = (us.attachments.filter(id__in=updated_ids)
                         .values("id", "order")
                         .order_by("order", "id"))
    assert response.json() == list(res)

    att1.refresh_from_db()
    att2.refresh_from_db()
    att3.refresh_from_db()
    assert att2.order == 1
    assert att3.order == 2
    assert att1.order == 3


def test_api_update_orders_in_bulk_succeeds_moved_to_the_middle(client):
    #
    # -------- |                     | --------
    #   att1   |   MOVE: att3, att1  |   att2
    #   att2   |   AFTER: att2       |   att3
    #   att3   |                     |   att1
    #

    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us = f.create_userstory(project=project)

    att1 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=1)
    att2 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=2)
    att3 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=3)

    url = reverse("userstory-attachments-bulk-update-order")

    data = {
        "object_id": us.id,
        "after_attachment_id": att2.id,
        "bulk_attachments": [att3.id,
                             att1.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200, response.data

    updated_ids = [
        att3.id,
        att1.id,
    ]
    res = (us.attachments.filter(id__in=updated_ids)
                         .values("id", "order")
                         .order_by("order", "id"))
    assert response.json() == list(res)

    att1.refresh_from_db()
    att2.refresh_from_db()
    att3.refresh_from_db()
    assert att2.order == 2
    assert att3.order == 3
    assert att1.order == 4


def test_api_update_orders_in_bulk_invalid_object_id(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us = f.create_userstory(project=project)

    att1 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=1)
    att2 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=2)
    att3 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=3)

    url = reverse("userstory-attachments-bulk-update-order")

    data = {
        "after_attachment_id": att2.id,
        "bulk_attachments": [att3.id,
                             att1.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "object_id" in response.data

    data["object_id"] = None

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "object_id" in response.data


def test_api_update_orders_in_bulk_invalid_attachments(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)

    att1 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=1)
    att2 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=2)
    att3 = f.UserStoryAttachmentFactory(project=us2.project, content_object=us2, order=3)

    url = reverse("userstory-attachments-bulk-update-order")

    data = {
        "object_id": us.id,
        "after_attachment_id": att2.id,
        "bulk_attachments": [att3.id,
                             att1.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "bulk_attachments" in response.data


def test_api_update_orders_in_bulk_invalid_after_attachment_because_object(client):
    project = f.create_project()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    us = f.create_userstory(project=project)
    us2 = f.create_userstory(project=project)

    att1 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=1)
    att2 = f.UserStoryAttachmentFactory(project=us.project, content_object=us, order=2)
    att3 = f.UserStoryAttachmentFactory(project=us2.project, content_object=us2, order=3)

    url = reverse("userstory-attachments-bulk-update-order")

    data = {
        "object_id": us.id,
        "after_attachment_id": att3.id,
        "bulk_attachments": [att2.id,
                             att1.id]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert len(response.data) == 1
    assert "after_attachment_id" in response.data
