# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
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
pytestmark = pytest.mark.django_db(transaction=True)


#########################################################
# Task Custom Attributes
#########################################################

def test_task_custom_attribute_duplicate_name_error_on_create(client):
    custom_attr_1 = f.TaskCustomAttributeFactory()
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)


    url = reverse("task-custom-attributes-list")
    data = {"name": custom_attr_1.name,
            "project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_task_custom_attribute_duplicate_name_error_on_update(client):
    custom_attr_1 = f.TaskCustomAttributeFactory()
    custom_attr_2 = f.TaskCustomAttributeFactory(project=custom_attr_1.project)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)


    url = reverse("task-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"name": custom_attr_1.name}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_task_custom_attribute_duplicate_name_error_on_move_between_projects(client):
    custom_attr_1 = f.TaskCustomAttributeFactory()
    custom_attr_2 = f.TaskCustomAttributeFactory(name=custom_attr_1.name)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)
    f.MembershipFactory(user=custom_attr_1.project.owner,
                        project=custom_attr_2.project,
                        is_owner=True)


    url = reverse("task-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


#########################################################
# Task Custom Attributes Values
#########################################################

def test_task_custom_attributes_values_list(client):
    member = f.MembershipFactory(is_owner=True)

    url = reverse("task-custom-attributes-values-list")

    client.login(member.user)
    response = client.json.get(url)
    assert response.status_code == 404


def test_task_custom_attributes_values_create(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)
    ct2_id = "{}".format(custom_attr_2.id)

    url = reverse("task-custom-attributes-values-list")
    data = {
        "task": task.id,
        "attributes_values": {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    }

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert json.loads(response.data["attributes_values"]) == data["attributes_values"]
    task = task.__class__.objects.get(id=task.id)
    assert task.custom_attributes_values.attributes_values == data["attributes_values"]


def test_task_custom_attributes_values_create_with_error_invalid_key(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)

    url = reverse("task-custom-attributes-values-list")
    data = {
        "task": task.id,
        "attributes_values": {
            ct1_id: "test_1",
            "123456": "test_2"
        },
    }

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_task_custom_attributes_values_update(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = f.TaskCustomAttributesValuesFactory(
        task=task,
        attributes_values= {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    )

    url = reverse("task-custom-attributes-values-detail", args=[task.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            ct2_id: "test_2_updated"
        },
        "version": custom_attrs_val.version
    }

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert json.loads(response.data["attributes_values"]) == data["attributes_values"]
    task = task.__class__.objects.get(id=task.id)
    assert task.custom_attributes_values.attributes_values == data["attributes_values"]


def test_task_custom_attributes_values_update_with_error_invalid_key(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = f.TaskCustomAttributesValuesFactory(
        task=task,
        attributes_values= {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    )
    url = reverse("task-custom-attributes-values-detail", args=[task.id])
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


def test_task_custom_attributes_values_delete(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)
    ct2_id = "{}".format(custom_attr_2.id)

    url = reverse("task-custom-attributes-values-detail", args=[task.id])
    custom_attrs_val = f.TaskCustomAttributesValuesFactory(
        task=task,
        attributes_values= {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    )

    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert task.__class__.objects.filter(id=task.id).exists()
    assert not custom_attrs_val.__class__.objects.filter(id=custom_attrs_val.id).exists()


def test_task_custom_attributes_values_delete_us(client):
    task = f.TaskFactory()
    member = f.MembershipFactory(user=task.project.owner,
                                 project=task.project,
                                 is_owner=True)

    custom_attr_1 = f.TaskCustomAttributeFactory(project=task.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.TaskCustomAttributeFactory(project=task.project)
    ct2_id = "{}".format(custom_attr_2.id)

    url = reverse("tasks-detail", args=[task.id])
    custom_attrs_val = f.TaskCustomAttributesValuesFactory(
        task=task,
        attributes_values= {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    )

    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert not task.__class__.objects.filter(id=task.id).exists()
    assert not custom_attrs_val.__class__.objects.filter(id=custom_attrs_val.id).exists()


#########################################################
# Test tristres triggers :-P
#########################################################

def test_trigger_update_userstorycustomvalues_afeter_remove_userstorycustomattribute():
    user_story = f.UserStoryFactory()
    member = f.MembershipFactory(user=user_story.project.owner,
                                 project=user_story.project,
                                 is_owner=True)

    custom_attr_1 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.UserStoryCustomAttributeFactory(project=user_story.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = f.UserStoryCustomAttributesValuesFactory(
        user_story=user_story,
        attributes_values= {
            ct1_id: "test_1",
            ct2_id: "test_2"
        },
    )

    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id in custom_attrs_val.attributes_values.keys()

    custom_attr_2.delete()
    custom_attrs_val = custom_attrs_val.__class__.objects.get(id=custom_attrs_val.id)

    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id not in custom_attrs_val.attributes_values.keys()
