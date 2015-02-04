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
from taiga.projects.custom_attributes import serializers
from taiga.permissions.permissions import MEMBERS_PERMISSIONS

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
                                        anon_permissions=['view_project'],
                                        public_permissions=['view_project'],
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=['view_project'],
                                          public_permissions=['view_project'],
                                          owner=m.project_owner)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)

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

    f.MembershipFactory(project=m.public_project,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_owner=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_owner=True)

    m.public_userstory_ca = f.UserStoryCustomAttributeFactory(project=m.public_project)
    m.private_userstory_ca1 = f.UserStoryCustomAttributeFactory(project=m.private_project1)
    m.private_userstory_ca2 = f.UserStoryCustomAttributeFactory(project=m.private_project2)

    m.public_task_ca = f.TaskCustomAttributeFactory(project=m.public_project)
    m.private_task_ca1 = f.TaskCustomAttributeFactory(project=m.private_project1)
    m.private_task_ca2 = f.TaskCustomAttributeFactory(project=m.private_project2)

    m.public_issue_ca = f.IssueCustomAttributeFactory(project=m.public_project)
    m.private_issue_ca1 = f.IssueCustomAttributeFactory(project=m.private_project1)
    m.private_issue_ca2 = f.IssueCustomAttributeFactory(project=m.private_project2)

    return m


#########################################################
# User Story Custom Fields
#########################################################

def test_userstory_status_retrieve(client, data):
    public_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.public_userstory_ca.pk})
    private1_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca1.pk})
    private2_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca2.pk})

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


def test_userstory_status_update(client, data):
    public_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.public_userstory_ca.pk})
    private1_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca1.pk})
    private2_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    userstory_ca_data = serializers.UserStoryCustomAttributeSerializer(data.public_userstory_ca).data
    userstory_ca_data["name"] = "test"
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'put', public_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    userstory_ca_data = serializers.UserStoryCustomAttributeSerializer(data.private_userstory_ca1).data
    userstory_ca_data["name"] = "test"
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'put', private1_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    userstory_ca_data = serializers.UserStoryCustomAttributeSerializer(data.private_userstory_ca2).data
    userstory_ca_data["name"] = "test"
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'put', private2_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 200]


def test_userstory_status_delete(client, data):
    public_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.public_userstory_ca.pk})
    private1_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca1.pk})
    private2_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca2.pk})

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


def test_userstory_status_list(client, data):
    url = reverse('userstory-custom-attributes-list')

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
    assert len(response.data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.json.get(url)
    assert len(response.data) == 3
    assert response.status_code == 200


def test_userstory_status_patch(client, data):
    public_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.public_userstory_ca.pk})
    private1_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca1.pk})
    private2_url = reverse('userstory-custom-attributes-detail', kwargs={"pk": data.private_userstory_ca2.pk})

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


def test_userstory_status_action_bulk_update_order(client, data):
    url = reverse('userstory-custom-attributes-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_userstory_custom_attributes": [(1,2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_userstory_custom_attributes": [(1,2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_userstory_custom_attributes": [(1,2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]


#########################################################
# Task Custom Fields
#########################################################

def test_task_status_retrieve(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})

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


def test_task_status_update(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})

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


def test_task_status_delete(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})

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


def test_task_status_list(client, data):
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
    assert len(response.data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.json.get(url)
    assert len(response.data) == 3
    assert response.status_code == 200


def test_task_status_patch(client, data):
    public_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.public_task_ca.pk})
    private1_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca1.pk})
    private2_url = reverse('task-custom-attributes-detail', kwargs={"pk": data.private_task_ca2.pk})

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


def test_task_status_action_bulk_update_order(client, data):
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


#########################################################
# Issue Custom Fields
#########################################################

def test_issue_status_retrieve(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

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


def test_issue_status_update(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.public_issue_ca).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', public_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.private_issue_ca1).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', private1_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_ca_data = serializers.IssueCustomAttributeSerializer(data.private_issue_ca2).data
    issue_ca_data["name"] = "test"
    issue_ca_data = json.dumps(issue_ca_data)
    results = helper_test_http_method(client, 'put', private2_url, issue_ca_data, users)
    assert results == [401, 403, 403, 403, 200]


def test_issue_status_delete(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

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


def test_issue_status_list(client, data):
    url = reverse('issue-custom-attributes-list')

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
    assert len(response.data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.json.get(url)
    assert len(response.data) == 3
    assert response.status_code == 200


def test_issue_status_patch(client, data):
    public_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.public_issue_ca.pk})
    private1_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca1.pk})
    private2_url = reverse('issue-custom-attributes-detail', kwargs={"pk": data.private_issue_ca2.pk})

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


def test_issue_status_action_bulk_update_order(client, data):
    url = reverse('issue-custom-attributes-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_custom_attributes": [(1,2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]
