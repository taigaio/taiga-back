# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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


from django.core.urlresolvers import reverse
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


#########################################################
# User Story Custom Attributes
#########################################################

def test_userstory_custom_attribute_duplicate_name_error_on_create(client):
    custom_attr_1 = f.UserStoryCustomAttributeFactory()
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)


    url = reverse("userstory-custom-attributes-list")
    data = {"name": custom_attr_1.name,
            "project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_userstory_custom_attribute_duplicate_name_error_on_update(client):
    custom_attr_1 = f.UserStoryCustomAttributeFactory()
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=custom_attr_1.project)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)


    url = reverse("userstory-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"name": custom_attr_1.name}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_userstory_custom_attribute_duplicate_name_error_on_move_between_projects(client):
    custom_attr_1 = f.UserStoryCustomAttributeFactory()
    custom_attr_2 = f.UserStoryCustomAttributeFactory(name=custom_attr_1.name)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_admin=True)
    f.MembershipFactory(user=custom_attr_1.project.owner,
                        project=custom_attr_2.project,
                        is_admin=True)


    url = reverse("userstory-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


#########################################################
# User Story Custom Attributes Values
#########################################################

def test_userstory_custom_attributes_values_when_create_us(client):
    user_story = f.UserStoryFactory()
    assert user_story.custom_attributes_values.attributes_values == {}


def test_userstory_custom_attributes_values_update(client):
    user_story = f.UserStoryFactory()
    member = f.MembershipFactory(user=user_story.project.owner,
                                 project=user_story.project,
                                 is_admin=True)

    custom_attr_1 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = user_story.custom_attributes_values

    url = reverse("userstory-custom-attributes-values-detail", args=[user_story.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            ct2_id: "test_2_updated"
        },
        "version": custom_attrs_val.version
    }

    assert user_story.custom_attributes_values.attributes_values == {}
    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["attributes_values"] == data["attributes_values"]
    user_story = user_story.__class__.objects.get(id=user_story.id)
    assert user_story.custom_attributes_values.attributes_values == data["attributes_values"]


def test_userstory_custom_attributes_values_update_with_error_invalid_key(client):
    user_story = f.UserStoryFactory()
    member = f.MembershipFactory(user=user_story.project.owner,
                                 project=user_story.project,
                                 is_admin=True)

    custom_attr_1 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=user_story.project)

    custom_attrs_val = user_story.custom_attributes_values

    url = reverse("userstory-custom-attributes-values-detail", args=[user_story.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            "123456": "test_2_updated"
        },
        "version": custom_attrs_val.version
    }

    assert user_story.custom_attributes_values.attributes_values == {}
    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


#########################################################
# Test tristres triggers :-P
#########################################################

def test_trigger_update_userstorycustomvalues_afeter_remove_userstorycustomattribute(client):
    user_story = f.UserStoryFactory()
    member = f.MembershipFactory(user=user_story.project.owner,
                                 project=user_story.project,
                                 is_admin=True)

    custom_attr_1 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = user_story.custom_attributes_values

    custom_attrs_val.attributes_values = {ct1_id: "test_1", ct2_id: "test_2"}
    custom_attrs_val.save()

    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id in custom_attrs_val.attributes_values.keys()

    url = reverse("userstory-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204

    custom_attrs_val = custom_attrs_val.__class__.objects.get(id=custom_attrs_val.id)
    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id not in custom_attrs_val.attributes_values.keys()
