# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.transaction import atomic
from django.urls import reverse
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


#########################################################
# Epic Custom Attributes
#########################################################

def test_epic_custom_attribute_duplicate_name_error_on_create(client):
    custom_attr_1 = f.EpicCustomAttributeFactory()
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)


    url = reverse("epic-custom-attributes-list")
    data = {"name": custom_attr_1.name,
            "project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_epic_custom_attribute_duplicate_name_error_on_update(client):
    custom_attr_1 = f.EpicCustomAttributeFactory()
    custom_attr_2 = f.EpicCustomAttributeFactory(project=custom_attr_1.project)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)


    url = reverse("epic-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"name": custom_attr_1.name}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_epic_custom_attribute_duplicate_name_error_on_move_between_projects(client):
    custom_attr_1 = f.EpicCustomAttributeFactory()
    custom_attr_2 = f.EpicCustomAttributeFactory(name=custom_attr_1.name)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)
    f.MembershipFactory(user=custom_attr_1.project.owner,
                        project=custom_attr_2.project,
                        is_admin=True)

    url = reverse("epic-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


#########################################################
# Epic Custom Attributes Values
#########################################################

def test_epic_custom_attributes_values_when_create_us(client):
    epic = f.EpicFactory()
    assert epic.custom_attributes_values.attributes_values == {}


def test_epic_custom_attributes_values_update(client):
    epic = f.EpicFactory()
    member = f.MembershipFactory(user=epic.project.owner,
                                 project=epic.project,
                                 is_admin=True)

    custom_attr_1 = f.EpicCustomAttributeFactory(project=epic.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.EpicCustomAttributeFactory(project=epic.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = epic.custom_attributes_values

    url = reverse("epic-custom-attributes-values-detail", args=[epic.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            ct2_id: "test_2_updated"
        },
        "version": custom_attrs_val.version
    }


    assert epic.custom_attributes_values.attributes_values == {}
    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["attributes_values"] == data["attributes_values"]
    epic = epic.__class__.objects.get(id=epic.id)
    assert epic.custom_attributes_values.attributes_values == data["attributes_values"]


def test_epic_custom_attributes_values_update_with_error_invalid_key(client):
    epic = f.EpicFactory()
    member = f.MembershipFactory(user=epic.project.owner,
                                 project=epic.project,
                                 is_admin=True)

    custom_attr_1 = f.EpicCustomAttributeFactory(project=epic.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.EpicCustomAttributeFactory(project=epic.project)

    custom_attrs_val = epic.custom_attributes_values

    url = reverse("epic-custom-attributes-values-detail", args=[epic.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            "123456": "test_2_updated"
        },
        "version": custom_attrs_val.version
    }

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400

def test_epic_custom_attributes_values_delete_epic(client):
    epic = f.EpicFactory()
    member = f.MembershipFactory(user=epic.project.owner,
                                 project=epic.project,
                                 is_admin=True)

    custom_attr_1 = f.EpicCustomAttributeFactory(project=epic.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.EpicCustomAttributeFactory(project=epic.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = epic.custom_attributes_values

    url = reverse("epics-detail", args=[epic.id])

    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert not epic.__class__.objects.filter(id=epic.id).exists()
    assert not custom_attrs_val.__class__.objects.filter(id=custom_attrs_val.id).exists()


#########################################################
# Test tristres triggers :-P
#########################################################

def test_trigger_update_epiccustomvalues_afeter_remove_epiccustomattribute(client):
    epic = f.EpicFactory()
    member = f.MembershipFactory(user=epic.project.owner,
                                 project=epic.project,
                                 is_admin=True)
    custom_attr_1 = f.EpicCustomAttributeFactory(project=epic.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.EpicCustomAttributeFactory(project=epic.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = epic.custom_attributes_values
    custom_attrs_val.attributes_values = {ct1_id: "test_1", ct2_id: "test_2"}
    custom_attrs_val.save()

    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id in custom_attrs_val.attributes_values.keys()

    url = reverse("epic-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204

    custom_attrs_val = custom_attrs_val.__class__.objects.get(id=custom_attrs_val.id)
    assert not custom_attr_2.__class__.objects.filter(pk=custom_attr_2.pk).exists()
    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id not in custom_attrs_val.attributes_values.keys()
