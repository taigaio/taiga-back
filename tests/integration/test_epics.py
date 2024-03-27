# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid
import csv

from unittest import mock

from django.urls import reverse

from taiga.base.utils import json
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.epics import services
from taiga.projects.epics import models
from taiga.projects.occ import OCCResourceMixin

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_invalid_csv(client):
    url = reverse("epics-csv")

    project = f.ProjectFactory.create(epics_csv_uuid=uuid.uuid4().hex)
    f.EpicFactory.create(project=project, epics_order=1, status=project.default_us_status)

    client.login(project.owner)
    response = client.get(url)
    assert response.status_code == 404

    response = client.get("{}?uuid={}".format(url, "not-valid-uuid"))
    assert response.status_code == 404


def test_get_valid_csv(client):
    url = reverse("epics-csv")
    project = f.ProjectFactory.create(epics_csv_uuid=uuid.uuid4().hex)

    response = client.get("{}?uuid={}".format(url, project.epics_csv_uuid))
    assert response.status_code == 200


def test_custom_fields_csv_generation():
    project = f.ProjectFactory.create(epics_csv_uuid=uuid.uuid4().hex)
    attr = f.EpicCustomAttributeFactory.create(project=project, name="attr1", description="desc")
    epic = f.EpicFactory.create(project=project)
    attr_values = epic.custom_attributes_values
    attr_values.attributes_values = {str(attr.id): "val1"}
    attr_values.save()
    queryset = project.epics.all()
    data = services.epics_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)

    assert row[19] == attr.name
    row = next(reader)
    assert row[19] == "val1"


def test_update_epic_order(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    epic_1 = f.EpicFactory.create(project=project, epics_order=1, status=project.default_us_status)
    epic_2 = f.EpicFactory.create(project=project, epics_order=2, status=project.default_us_status)
    epic_3 = f.EpicFactory.create(project=project, epics_order=3, status=project.default_us_status)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    url = reverse('epics-detail', kwargs={"pk": epic_1.pk})
    data = {
        "epics_order": 2,
        "version": epic_1.version
    }

    client.login(user)
    response = client.json.patch(url, json.dumps(data))
    assert json.loads(response.get("taiga-info-order-updated")) == {
        str(epic_1.id): 2,
        str(epic_2.id): 3,
        str(epic_3.id): 4
    }


def test_bulk_create_related_userstories(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    epic = f.EpicFactory.create(project=project)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)

    url = reverse('epics-related-userstories-bulk-create', args=[epic.pk])

    data = {
        "bulk_userstories": "test1\ntest2",
        "project_id": project.id
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    assert len(response.data) == 2


def test_bulk_create_related_userstories_with_default_swimlane_and_kanban_enable(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    swimlane = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    epic = f.EpicFactory.create(project=project)

    project.default_swimlane = swimlane
    project.is_kanban_activated = True
    project.save()

    url = reverse('epics-related-userstories-bulk-create', args=[epic.pk])

    data = {
        "bulk_userstories": "test1\ntest2",
        "project_id": project.id
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    assert len(response.data) == 2

    userstories = epic.user_stories.all()
    assert userstories[0].swimlane == swimlane
    assert userstories[1].swimlane == swimlane


def test_bulk_create_related_userstories_with_default_swimlane_and_kanban_disable(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    f.MembershipFactory.create(project=project, user=user, is_admin=True)
    swimlane = f.SwimlaneFactory.create(project=project)
    swimlane2 = f.SwimlaneFactory.create(project=project)
    epic = f.EpicFactory.create(project=project)

    project.default_swimlane = swimlane
    project.is_kanban_activated = False
    project.save()

    url = reverse('epics-related-userstories-bulk-create', args=[epic.pk])

    data = {
        "bulk_userstories": "test1\ntest2",
        "project_id": project.id
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 200
    assert len(response.data) == 2

    userstories = epic.user_stories.all()
    assert userstories[0].swimlane == None
    assert userstories[1].swimlane == None


def test_set_related_userstory(client):
    user = f.UserFactory.create()
    epic = f.EpicFactory.create()
    us = f.UserStoryFactory.create()
    f.MembershipFactory.create(project=epic.project, user=user, is_admin=True)
    f.MembershipFactory.create(project=us.project, user=user, is_admin=True)

    url = reverse('epics-related-userstories-list', args=[epic.pk])

    data = {
        "user_story": us.id,
        "epic": epic.pk
    }
    client.login(user)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 201


def test_set_related_userstory_existing(client):
    user = f.UserFactory.create()
    epic = f.EpicFactory.create()
    us = f.UserStoryFactory.create()
    related_us = f.RelatedUserStory.create(epic=epic, user_story=us, order=55)
    f.MembershipFactory.create(project=epic.project, user=user, is_admin=True)
    f.MembershipFactory.create(project=us.project, user=user, is_admin=True)

    url = reverse('epics-related-userstories-detail', args=[epic.pk, us.pk])
    data = {
        "order": 77
    }
    client.login(user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200

    related_us.refresh_from_db()
    assert related_us.order == 77


def test_unset_related_userstory(client):
    user = f.UserFactory.create()
    epic = f.EpicFactory.create()
    us = f.UserStoryFactory.create()
    related_us = f.RelatedUserStory.create(epic=epic, user_story=us, order=55)
    f.MembershipFactory.create(project=epic.project, user=user, is_admin=True)

    url = reverse('epics-related-userstories-detail', args=[epic.pk, us.id])

    client.login(user)
    response = client.delete(url)
    assert response.status_code == 204
    assert not models.RelatedUserStory.objects.filter(id=related_us.id).exists()


def test_api_validator_assigned_to_when_update_epics(client):
    project = f.create_project(anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                               public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)))
    project_member_owner = f.MembershipFactory.create(project=project,
                                                      user=project.owner,
                                                      is_admin=True,
                                                      role__project=project,
                                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_member = f.MembershipFactory.create(project=project,
                                                is_admin=True,
                                                role__project=project,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_no_member = f.MembershipFactory.create(is_admin=True)

    epic = f.create_epic(project=project, owner=project.owner, status=project.epic_statuses.all()[0])

    url = reverse('epics-detail', kwargs={"pk": epic.pk})

    # assign
    data = {
        "assigned_to": project_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 200, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == project_member.user.id

    # unassign
    data = {
        "assigned_to": None,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 200, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == None

    # assign to invalid user
    data = {
        "assigned_to": project_no_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.patch(url, json.dumps(data))
        assert response.status_code == 400, response.data


def test_api_validator_assigned_to_when_create_epics(client):
    project = f.create_project(anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                               public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)))
    project_member_owner = f.MembershipFactory.create(project=project,
                                                      user=project.owner,
                                                      is_admin=True,
                                                      role__project=project,
                                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_member = f.MembershipFactory.create(project=project,
                                                is_admin=True,
                                                role__project=project,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    project_no_member = f.MembershipFactory.create(is_admin=True)

    url = reverse('epics-list')

    # assign
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": project_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == project_member.user.id

    # unassign
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": None,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 201, response.data
        assert "assigned_to" in response.data
        assert response.data["assigned_to"] == None

    # assign to invalid user
    data = {
        "subject": "test",
        "project": project.id,
        "assigned_to": project_no_member.user.id,
    }

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        client.login(project.owner)

        response = client.json.post(url, json.dumps(data))
        assert response.status_code == 400, response.data
