# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.urls import reverse

from taiga.base.utils import json
from taiga.projects import choices as project_choices
from taiga.projects.custom_attributes import serializers
from taiga.permissions.choices import (MEMBERS_PERMISSIONS,
                                           ANON_PERMISSIONS)

from tests import factories as f
from tests.utils import helper_test_http_method

import pytest
pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    m = type("Models", (object,), {})
    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()
    m.superuser = f.UserFactory.create(is_superuser=True)

    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          owner=m.project_owner)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)
    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF)

    m.public_membership = f.MembershipFactory(project=m.public_project,
                                          user=m.project_member_with_perms,
                                          email=m.project_member_with_perms.email,
                                          role__project=m.public_project,
                                          role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(project=m.private_project1,
                                                user=m.project_member_with_perms,
                                                email=m.project_member_with_perms.email,
                                                role__project=m.private_project1,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        email=m.project_member_without_perms.email,
                        role__project=m.private_project1,
                        role__permissions=[])

    m.private_membership2 = f.MembershipFactory(project=m.private_project2,
                                                user=m.project_member_with_perms,
                                                email=m.project_member_with_perms.email,
                                                role__project=m.private_project2,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
                        email=m.project_member_without_perms.email,
                        role__project=m.private_project2,
                        role__permissions=[])

    m.blocked_membership = f.MembershipFactory(project=m.blocked_project,
                                                user=m.project_member_with_perms,
                                                email=m.project_member_with_perms.email,
                                                role__project=m.blocked_project,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.blocked_project,
                        user=m.project_member_without_perms,
                        email=m.project_member_without_perms.email,
                        role__project=m.blocked_project,
                        role__permissions=[])

    f.MembershipFactory(project=m.public_project,
                        user=m.project_owner,
                        is_admin=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_admin=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_admin=True)

    f.MembershipFactory(project=m.blocked_project,
                        user=m.project_owner,
                        is_admin=True)

    m.public_task_ca = f.TaskCustomAttributeFactory(project=m.public_project)
    m.private_task_ca1 = f.TaskCustomAttributeFactory(project=m.private_project1)
    m.private_task_ca2 = f.TaskCustomAttributeFactory(project=m.private_project2)
    m.blocked_task_ca = f.TaskCustomAttributeFactory(project=m.blocked_project)

    m.public_task = f.TaskFactory(project=m.public_project,
                                  status__project=m.public_project,
                                  milestone__project=m.public_project,
                                  user_story__project=m.public_project)
    m.private_task1 = f.TaskFactory(project=m.private_project1,
                                    status__project=m.private_project1,
                                    milestone__project=m.private_project1,
                                    user_story__project=m.private_project1)
    m.private_task2 = f.TaskFactory(project=m.private_project2,
                                    status__project=m.private_project2,
                                    milestone__project=m.private_project2,
                                    user_story__project=m.private_project2)
    m.blocked_task = f.TaskFactory(project=m.blocked_project,
                                    status__project=m.blocked_project,
                                    milestone__project=m.blocked_project,
                                    user_story__project=m.blocked_project)

    m.public_task_cav = m.public_task.custom_attributes_values
    m.private_task_cav1 = m.private_task1.custom_attributes_values
    m.private_task_cav2 = m.private_task2.custom_attributes_values
    m.blocked_task_cav = m.blocked_task.custom_attributes_values

    return m


#########################################################
# Task Custom Attribute
#########################################################

def test_task_custom_attribute_retrieve(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})
    blocked_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.blocked_task_ca.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_task_custom_attribute_create(client, data):
    public_url = reverse('task-custom-attributes-list')
    private1_url = reverse('task-custom-attributes-list')
    private2_url = reverse('task-custom-attributes-list')
    blocked_url = reverse('task-custom-attributes-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    task_ca_data = {"name": "test-new", "project": data.public_project.id}
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'post', public_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    task_ca_data = {"name": "test-new", "project": data.private_project1.id}
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'post', private1_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    task_ca_data = {"name": "test-new", "project": data.private_project2.id}
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'post', private2_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    task_ca_data = {"name": "test-new", "project": data.blocked_project.id}
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'post', blocked_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_task_custom_attribute_update(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})
    blocked_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.blocked_task_ca.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    task_ca_data = serializers.TaskCustomAttributeSerializer(data.public_task_ca).data
    task_ca_data["name"] = "test"
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'put', public_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_ca_data = serializers.TaskCustomAttributeSerializer(data.private_task_ca1).data
    task_ca_data["name"] = "test"
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'put', private1_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_ca_data = serializers.TaskCustomAttributeSerializer(data.private_task_ca2).data
    task_ca_data["name"] = "test"
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'put', private2_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_ca_data = serializers.TaskCustomAttributeSerializer(data.blocked_task_ca).data
    task_ca_data["name"] = "test"
    task_ca_data = json.dumps(task_ca_data)
    results = helper_test_http_method(client, 'put', private2_url, task_ca_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_task_custom_attribute_delete(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})
    blocked_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.blocked_task_ca.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private1_url, None, users)
    assert results == [401, 403, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private2_url, None, users)
    assert results == [401, 403, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [401, 403, 403, 403, 451]



def test_task_custom_attribute_list(client, data):
    url = reverse('task-custom-attributes-list')

    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.json.get(url)
    assert len(response.data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.json.get(url)
    assert len(response.data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.json.get(url)
    assert len(response.data) == 4
    assert response.status_code == 200


def test_task_custom_attribute_patch(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})
    blocked_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.blocked_task_ca.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'patch', public_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'patch', private1_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'patch', private2_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'patch', blocked_url, '{"name": "Test"}', users)
    assert results == [401, 403, 403, 403, 451]


def test_task_custom_attribute_action_bulk_update_order(client, data):
    url = reverse('task-custom-attributes-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_task_custom_attributes": [(1,2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_custom_attributes": [(1,2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_custom_attributes": [(1,2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_custom_attributes": [(1,2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]

#########################################################
# Task Custom Attribute
#########################################################


def test_task_custom_attributes_values_retrieve(client, data):
    public_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.public_task.pk})
    private_url1 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task1.pk})
    private_url2 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task2.pk})
    blocked_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.blocked_task.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_task_custom_attributes_values_update(client, data):
    public_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.public_task.pk})
    private_url1 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task1.pk})
    private_url2 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task2.pk})
    blocked_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.blocked_task.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    task_data = serializers.TaskCustomAttributesValuesSerializer(data.public_task_cav).data
    task_data["attributes_values"] = {str(data.public_task_ca.pk): "test"}
    task_data = json.dumps(task_data)
    results = helper_test_http_method(client, 'put', public_url, task_data, users)
    assert results == [401, 403, 403, 200, 200]

    task_data = serializers.TaskCustomAttributesValuesSerializer(data.private_task_cav1).data
    task_data["attributes_values"] = {str(data.private_task_ca1.pk): "test"}
    task_data = json.dumps(task_data)
    results = helper_test_http_method(client, 'put', private_url1, task_data, users)
    assert results == [401, 403, 403, 200, 200]

    task_data = serializers.TaskCustomAttributesValuesSerializer(data.private_task_cav2).data
    task_data["attributes_values"] = {str(data.private_task_ca2.pk): "test"}
    task_data = json.dumps(task_data)
    results = helper_test_http_method(client, 'put', private_url2, task_data, users)
    assert results == [401, 403, 403, 200, 200]

    task_data = serializers.TaskCustomAttributesValuesSerializer(data.blocked_task_cav).data
    task_data["attributes_values"] = {str(data.blocked_task_ca.pk): "test"}
    task_data = json.dumps(task_data)
    results = helper_test_http_method(client, 'put', blocked_url, task_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_task_custom_attributes_values_patch(client, data):
    public_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.public_task.pk})
    private_url1 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task1.pk})
    private_url2 = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.private_task2.pk})
    blocked_url = reverse('task-custom-attributes-values-detail', kwargs={"task_id": data.blocked_task.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    patch_data = json.dumps({"attributes_values": {str(data.public_task_ca.pk): "test"},
                             "version": data.public_task.version})
    results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"attributes_values": {str(data.private_task_ca1.pk): "test"},
                             "version": data.private_task1.version})
    results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"attributes_values": {str(data.private_task_ca2.pk): "test"},
                             "version": data.private_task2.version})
    results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"attributes_values": {str(data.blocked_task_ca.pk): "test"},
                             "version": data.blocked_task.version})
    results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
    assert results == [401, 403, 403, 451, 451]
