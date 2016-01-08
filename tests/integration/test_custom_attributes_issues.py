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


from django.db.transaction import atomic
from django.core.urlresolvers import reverse
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


#########################################################
# Issue Custom Attributes
#########################################################

def test_issue_custom_attribute_duplicate_name_error_on_create(client):
    custom_attr_1 = f.IssueCustomAttributeFactory()
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)


    url = reverse("issue-custom-attributes-list")
    data = {"name": custom_attr_1.name,
            "project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 400


def test_issue_custom_attribute_duplicate_name_error_on_update(client):
    custom_attr_1 = f.IssueCustomAttributeFactory()
    custom_attr_2 = f.IssueCustomAttributeFactory(project=custom_attr_1.project)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)


    url = reverse("issue-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"name": custom_attr_1.name}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


def test_issue_custom_attribute_duplicate_name_error_on_move_between_projects(client):
    custom_attr_1 = f.IssueCustomAttributeFactory()
    custom_attr_2 = f.IssueCustomAttributeFactory(name=custom_attr_1.name)
    member = f.MembershipFactory(user=custom_attr_1.project.owner,
                                 project=custom_attr_1.project,
                                 is_owner=True)
    f.MembershipFactory(user=custom_attr_1.project.owner,
                        project=custom_attr_2.project,
                        is_owner=True)


    url = reverse("issue-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    data = {"project": custom_attr_1.project.pk}

    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400


#########################################################
# Issue Custom Attributes Values
#########################################################

def test_issue_custom_attributes_values_when_create_us(client):
    issue = f.IssueFactory()
    assert issue.custom_attributes_values.attributes_values == {}


def test_issue_custom_attributes_values_update(client):
    issue = f.IssueFactory()
    member = f.MembershipFactory(user=issue.project.owner,
                                 project=issue.project,
                                 is_owner=True)

    custom_attr_1 = f.IssueCustomAttributeFactory(project=issue.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.IssueCustomAttributeFactory(project=issue.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = issue.custom_attributes_values

    url = reverse("issue-custom-attributes-values-detail", args=[issue.id])
    data = {
        "attributes_values": {
            ct1_id: "test_1_updated",
            ct2_id: "test_2_updated"
        },
        "version": custom_attrs_val.version
    }


    assert issue.custom_attributes_values.attributes_values == {}
    client.login(member.user)
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200
    assert response.data["attributes_values"] == data["attributes_values"]
    issue = issue.__class__.objects.get(id=issue.id)
    assert issue.custom_attributes_values.attributes_values == data["attributes_values"]


def test_issue_custom_attributes_values_update_with_error_invalid_key(client):
    issue = f.IssueFactory()
    member = f.MembershipFactory(user=issue.project.owner,
                                 project=issue.project,
                                 is_owner=True)

    custom_attr_1 = f.IssueCustomAttributeFactory(project=issue.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.IssueCustomAttributeFactory(project=issue.project)

    custom_attrs_val = issue.custom_attributes_values

    url = reverse("issue-custom-attributes-values-detail", args=[issue.id])
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

def test_issue_custom_attributes_values_delete_issue(client):
    issue = f.IssueFactory()
    member = f.MembershipFactory(user=issue.project.owner,
                                 project=issue.project,
                                 is_owner=True)

    custom_attr_1 = f.IssueCustomAttributeFactory(project=issue.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.IssueCustomAttributeFactory(project=issue.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = issue.custom_attributes_values

    url = reverse("issues-detail", args=[issue.id])

    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204
    assert not issue.__class__.objects.filter(id=issue.id).exists()
    assert not custom_attrs_val.__class__.objects.filter(id=custom_attrs_val.id).exists()


#########################################################
# Test tristres triggers :-P
#########################################################

def test_trigger_update_issuecustomvalues_afeter_remove_issuecustomattribute(client):
    issue = f.IssueFactory()
    member = f.MembershipFactory(user=issue.project.owner,
                                 project=issue.project,
                                 is_owner=True)
    custom_attr_1 = f.IssueCustomAttributeFactory(project=issue.project)
    ct1_id = "{}".format(custom_attr_1.id)
    custom_attr_2 = f.IssueCustomAttributeFactory(project=issue.project)
    ct2_id = "{}".format(custom_attr_2.id)

    custom_attrs_val = issue.custom_attributes_values
    custom_attrs_val.attributes_values = {ct1_id: "test_1", ct2_id: "test_2"}
    custom_attrs_val.save()

    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id in custom_attrs_val.attributes_values.keys()

    url = reverse("issue-custom-attributes-detail", kwargs={"pk": custom_attr_2.pk})
    client.login(member.user)
    response = client.json.delete(url)
    assert response.status_code == 204

    custom_attrs_val = custom_attrs_val.__class__.objects.get(id=custom_attrs_val.id)
    assert not custom_attr_2.__class__.objects.filter(pk=custom_attr_2.pk).exists()
    assert ct1_id in custom_attrs_val.attributes_values.keys()
    assert ct2_id not in custom_attrs_val.attributes_values.keys()
