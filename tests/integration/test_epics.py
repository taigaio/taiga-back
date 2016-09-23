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

import uuid
import csv

from unittest import mock

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.epics import services
from taiga.projects.epics import models

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_invalid_csv(client):
    url = reverse("epics-csv")

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
    attr_values.attributes_values = {str(attr.id):"val1"}
    attr_values.save()
    queryset = project.epics.all()
    data = services.epics_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)
    assert row[18] == attr.name
    row = next(reader)
    assert row[18] == "val1"


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
