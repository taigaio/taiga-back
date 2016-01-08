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
from taiga.projects.custom_attributes import serializers
from taiga.permissions.permissions import (MEMBERS_PERMISSIONS,
                                           ANON_PERMISSIONS, USER_PERMISSIONS)


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
                                        public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                        owner=m.project_owner)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
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


    m.public_user_story = f.UserStoryFactory(project=m.public_project,
                                             status__project=m.public_project)
    m.private_user_story1 = f.UserStoryFactory(project=m.private_project1,
                                               status__project=m.private_project1)
    m.private_user_story2 = f.UserStoryFactory(project=m.private_project2,
                                               status__project=m.private_project2)

    m.public_user_story_cav = m.public_user_story.custom_attributes_values
    m.private_user_story_cav1 = m.private_user_story1.custom_attributes_values
    m.private_user_story_cav2 = m.private_user_story2.custom_attributes_values

    return m


#########################################################
# User Story Custom Attribute
#########################################################

def test_userstory_custom_attribute_retrieve(client, data):
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


def test_userstory_custom_attribute_create(client, data):
    public_url = reverse('userstory-custom-attributes-list')
    private1_url = reverse('userstory-custom-attributes-list')
    private2_url = reverse('userstory-custom-attributes-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    userstory_ca_data = {"name": "test-new", "project": data.public_project.id}
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'post', public_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    userstory_ca_data = {"name": "test-new", "project": data.private_project1.id}
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'post', private1_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 201]

    userstory_ca_data = {"name": "test-new", "project": data.private_project2.id}
    userstory_ca_data = json.dumps(userstory_ca_data)
    results = helper_test_http_method(client, 'post', private2_url, userstory_ca_data, users)
    assert results == [401, 403, 403, 403, 201]


def test_userstory_custom_attribute_update(client, data):
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


def test_userstory_custom_attribute_delete(client, data):
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


def test_userstory_custom_attribute_list(client, data):
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


def test_userstory_custom_attribute_patch(client, data):
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


def test_userstory_custom_attribute_action_bulk_update_order(client, data):
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
# UserStory Custom Attribute
#########################################################


def test_userstory_custom_attributes_values_retrieve(client, data):
    public_url = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.public_user_story.pk})
    private_url1 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story1.pk})
    private_url2 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story2.pk})

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


def test_userstory_custom_attributes_values_update(client, data):
    public_url = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.public_user_story.pk})
    private_url1 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story1.pk})
    private_url2 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    user_story_data = serializers.UserStoryCustomAttributesValuesSerializer(data.public_user_story_cav).data
    user_story_data["attributes_values"] = {str(data.public_userstory_ca.pk): "test"}
    user_story_data = json.dumps(user_story_data)
    results = helper_test_http_method(client, 'put', public_url, user_story_data, users)
    assert results == [401, 403, 403, 200, 200]

    user_story_data = serializers.UserStoryCustomAttributesValuesSerializer(data.private_user_story_cav1).data
    user_story_data["attributes_values"] = {str(data.private_userstory_ca1.pk): "test"}
    user_story_data = json.dumps(user_story_data)
    results = helper_test_http_method(client, 'put', private_url1, user_story_data, users)
    assert results == [401, 403, 403, 200, 200]

    user_story_data = serializers.UserStoryCustomAttributesValuesSerializer(data.private_user_story_cav2).data
    user_story_data["attributes_values"] = {str(data.private_userstory_ca2.pk): "test"}
    user_story_data = json.dumps(user_story_data)
    results = helper_test_http_method(client, 'put', private_url2, user_story_data, users)
    assert results == [401, 403, 403, 200, 200]


def test_userstory_custom_attributes_values_patch(client, data):
    public_url = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.public_user_story.pk})
    private_url1 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story1.pk})
    private_url2 = reverse('userstory-custom-attributes-values-detail', kwargs={
                                    "user_story_id": data.private_user_story2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    patch_data = json.dumps({"attributes_values": {str(data.public_userstory_ca.pk): "test"},
                             "version": data.public_user_story.version})
    results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"attributes_values": {str(data.private_userstory_ca1.pk): "test"},
                             "version": data.private_user_story1.version})
    results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    patch_data = json.dumps({"attributes_values": {str(data.private_userstory_ca2.pk): "test"},
                             "version": data.private_user_story2.version})
    results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
    assert results == [401, 403, 403, 200, 200]
