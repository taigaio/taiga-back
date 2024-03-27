# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid

from django.urls import reverse

from taiga.base.utils import json
from taiga.projects import choices as project_choices
from taiga.projects.models import Project
from taiga.projects.utils import attach_extra_info as attach_project_extra_info
from taiga.projects.userstories.models import UserStory
from taiga.projects.userstories.serializers import UserStorySerializer
from taiga.projects.userstories.utils import attach_extra_info as attach_userstory_extra_info
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.occ import OCCResourceMixin

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals
from taiga.projects.votes.services import add_vote
from taiga.projects.notifications.services import add_watcher

from unittest import mock

import pytest
pytestmark = pytest.mark.django_db


def setup_function(function):
    disconnect_signals()


def teardown_function(function):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()


    m.public_points = f.PointsFactory()
    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)) + ["comment_us"],
                                        owner=m.project_owner,
                                        userstories_csv_uuid=uuid.uuid4().hex,
                                        default_points=m.public_points)
    m.public_project = attach_project_extra_info(Project.objects.all()).get(id=m.public_project.id)

    m.private_points1 = f.PointsFactory()
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          owner=m.project_owner,
                                          userstories_csv_uuid=uuid.uuid4().hex,
                                          default_points=m.private_points1)
    m.private_project1 = attach_project_extra_info(Project.objects.all()).get(id=m.private_project1.id)

    m.private_sprint1 = f.MilestoneFactory.create(project=m.private_project1,
                                                  owner=m.project_owner)

    m.private_points2 = f.PointsFactory()
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner,
                                          userstories_csv_uuid=uuid.uuid4().hex,
                                          default_points=m.private_points2)
    m.private_project2 = attach_project_extra_info(Project.objects.all()).get(id=m.private_project2.id)

    m.blocked_points = f.PointsFactory()
    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         userstories_csv_uuid=uuid.uuid4().hex,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF,
                                         default_points=m.blocked_points)
    m.blocked_project = attach_project_extra_info(Project.objects.all()).get(id=m.blocked_project.id)

    m.public_membership = f.MembershipFactory(
        project=m.public_project,
        user=m.project_member_with_perms,
        role__project=m.public_project,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(
        project=m.private_project1,
        user=m.project_member_with_perms,
        role__project=m.private_project1,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        role__project=m.private_project1,
                        role__permissions=[])
    m.private_membership2 = f.MembershipFactory(
        project=m.private_project2,
        user=m.project_member_with_perms,
        role__project=m.private_project2,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
                        role__project=m.private_project2,
                        role__permissions=[])
    m.blocked_membership = f.MembershipFactory(
        project=m.blocked_project,
        user=m.project_member_with_perms,
        role__project=m.blocked_project,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.blocked_project,
                        user=m.project_member_without_perms,
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

    m.public_user_story = f.UserStoryFactory(project=m.public_project,
                                             milestone__project=m.public_project,
                                             status__project=m.public_project)
    m.public_user_story = attach_userstory_extra_info(UserStory.objects.all()).get(id=m.public_user_story.id)

    m.private_user_story1 = f.UserStoryFactory(project=m.private_project1,
                                             milestone__project=m.private_project1,
                                             status__project=m.private_project1)
    m.private_user_story1 = attach_userstory_extra_info(UserStory.objects.all()).get(id=m.private_user_story1.id)

    m.private_user_story2 = f.UserStoryFactory(project=m.private_project2,
                                             milestone__project=m.private_project2,
                                             status__project=m.private_project2)
    m.private_user_story2 = attach_userstory_extra_info(UserStory.objects.all()).get(id=m.private_user_story2.id)

    m.blocked_user_story = f.UserStoryFactory(project=m.blocked_project,
                                             milestone__project=m.blocked_project,
                                             status__project=m.blocked_project)
    m.blocked_user_story = attach_userstory_extra_info(UserStory.objects.all()).get(id=m.blocked_user_story.id)

    return m


def test_user_story_list(client, data):
    url = reverse('userstories-list')

    response = client.get(url)
    userstories_data = json.loads(response.content.decode('utf-8'))
    assert len(userstories_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    userstories_data = json.loads(response.content.decode('utf-8'))
    assert len(userstories_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    userstories_data = json.loads(response.content.decode('utf-8'))
    assert len(userstories_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    userstories_data = json.loads(response.content.decode('utf-8'))
    assert len(userstories_data) == 4
    assert response.status_code == 200


def test_user_story_retrieve(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

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


def test_user_story_create(client, data):
    url = reverse('userstories-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({"subject": "test", "ref": 1, "project": data.public_project.pk})
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({"subject": "test", "ref": 2, "project": data.private_project1.pk})
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({"subject": "test", "ref": 3, "project": data.private_project2.pk})
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({"subject": "test", "ref": 4, "project": data.blocked_project.pk})
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_user_story_put_update(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        user_story_data = UserStorySerializer(data.public_user_story).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', public_url, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story1).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url1, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story2).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url2, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.blocked_user_story).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', blocked_url, user_story_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_put_comment(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        user_story_data = UserStorySerializer(data.public_user_story).data
        del user_story_data["points"]
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', public_url, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story1).data
        del user_story_data["points"]
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url1, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story2).data
        del user_story_data["points"]
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url2, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.blocked_user_story).data
        del user_story_data["points"]
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', blocked_url, user_story_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_put_update_and_comment(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        user_story_data = UserStorySerializer(data.public_user_story).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', public_url, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story1).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url1, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.private_user_story2).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', private_url2, user_story_data, users)
        assert results == [401, 403, 403, 200, 200]

        user_story_data = UserStorySerializer(data.blocked_user_story).data
        del user_story_data["points"]
        user_story_data["subject"] = "test"
        user_story_data["comment"] = "test comment"
        user_story_data = json.dumps(user_story_data)
        results = helper_test_http_method(client, 'put', blocked_url, user_story_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_put_update_with_project_change(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    user3 = f.UserFactory.create()
    user4 = f.UserFactory.create()
    project1 = f.ProjectFactory()
    project2 = f.ProjectFactory()

    us_status1 = f.UserStoryStatusFactory.create(project=project1)
    us_status2 = f.UserStoryStatusFactory.create(project=project2)
    points1 = f.PointsFactory.create(project=project1)
    points2 = f.PointsFactory.create(project=project2)

    project1.default_us_status = us_status1
    project2.default_us_status = us_status2
    project1.default_points = points1
    project2.default_points = points2

    project1.save()
    project2.save()

    project1 = attach_project_extra_info(Project.objects.all()).get(id=project1.id)
    project2 = attach_project_extra_info(Project.objects.all()).get(id=project2.id)

    f.MembershipFactory(project=project1,
                        user=user1,
                        role__project=project1,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=project2,
                        user=user1,
                        role__project=project2,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=project1,
                        user=user2,
                        role__project=project1,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=project2,
                        user=user3,
                        role__project=project2,
                        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    us = f.UserStoryFactory.create(project=project1)
    us = attach_userstory_extra_info(UserStory.objects.all()).get(id=us.id)

    url = reverse('userstories-detail', kwargs={"pk": us.pk})

    # Test user with permissions in both projects
    client.login(user1)

    us_data = UserStorySerializer(us).data
    us_data["project"] = project2.id
    del us_data["points"]
    us_data = json.dumps(us_data)

    response = client.put(url, data=us_data, content_type="application/json")

    assert response.status_code == 200

    us.project = project1
    us.save()

    # Test user with permissions in only origin project
    client.login(user2)

    us_data = UserStorySerializer(us).data
    us_data["project"] = project2.id
    del us_data["points"]
    us_data = json.dumps(us_data)

    response = client.put(url, data=us_data, content_type="application/json")

    assert response.status_code == 403

    us.project = project1
    us.save()

    # Test user with permissions in only destionation project
    client.login(user3)

    us_data = UserStorySerializer(us).data
    us_data["project"] = project2.id
    del us_data["points"]
    us_data = json.dumps(us_data)

    response = client.put(url, data=us_data, content_type="application/json")

    assert response.status_code == 403

    us.project = project1
    us.save()

    # Test user without permissions in the projects
    client.login(user4)

    us_data = UserStorySerializer(us).data
    us_data["project"] = project2.id
    del us_data["points"]
    us_data = json.dumps(us_data)

    response = client.put(url, data=us_data, content_type="application/json")

    assert response.status_code == 403

    us.project = project1
    us.save()


def test_user_story_patch_update(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        patch_data = json.dumps({"subject": "test", "version": data.public_user_story.version})
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.private_user_story1.version})
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.private_user_story2.version})
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.blocked_user_story.version})
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_patch_comment(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        patch_data = json.dumps({"comment": "test comment", "version": data.public_user_story.version})
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 200, 200, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.private_user_story1.version})
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.private_user_story2.version})
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.blocked_user_story.version})
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_patch_update_and_comment(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.public_user_story.version
        })
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.private_user_story1.version
        })
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.private_user_story2.version
        })
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.blocked_user_story.version
        })
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_user_story_delete(client, data):
    public_url = reverse('userstories-detail', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-detail', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-detail', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-detail', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
    ]
    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url1, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', private_url2, None, users)
    assert results == [401, 403, 403, 204]
    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [401, 403, 403, 451]


def test_user_story_action_bulk_create(client, data):
    url = reverse('userstories-bulk-create')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = json.dumps({"bulk_stories": "test1\ntest2", "project_id": data.public_user_story.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({"bulk_stories": "test1\ntest2", "project_id": data.private_user_story1.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({"bulk_stories": "test1\ntest2", "project_id": data.private_user_story2.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({"bulk_stories": "test1\ntest2", "project_id": data.blocked_user_story.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_user_story_action_bulk_update_order(client, data):
    url = reverse('userstories-bulk-update-backlog-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_userstories": [data.public_user_story.id],
        "project_id": data.public_project.pk,
        "after_userstory_id": None,
        "milestone_id": None,
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 200, 200]

    post_data = json.dumps({
        "bulk_userstories": [data.private_user_story1.id],
        "project_id": data.private_project1.pk,
        "after_userstory_id": None,
        "milestone_id": None,
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 200, 200]

    post_data = json.dumps({
        "bulk_userstories": [data.private_user_story2.id],
        "project_id": data.private_project2.pk,
        "after_userstory_id": None,
        "milestone_id": None,
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 200, 200]

    post_data = json.dumps({
        "bulk_userstories": [data.blocked_user_story.id],
        "project_id": data.blocked_project.pk,
        "after_userstory_id": None,
        "milestone_id": None,
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_user_story_action_bulk_update_milestone(client, data):
    url = reverse('userstories-bulk-update-milestone')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_stories": [
            {"us_id": data.private_user_story1.id, "order": 2}
        ],
        "milestone_id": data.private_sprint1.pk,
        "project_id": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 204, 204]


def test_user_story_action_upvote(client, data):
    public_url = reverse('userstories-upvote', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-upvote', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-upvote', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-upvote', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [401, 404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, "", users)
    assert results == [401, 404, 404, 451, 451]


def test_user_story_action_downvote(client, data):
    public_url = reverse('userstories-downvote', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-downvote', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-downvote', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-downvote', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [401, 404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, "", users)
    assert results == [401, 404, 404, 451, 451]


def test_user_story_voters_list(client, data):
    public_url = reverse('userstory-voters-list', kwargs={"resource_id": data.public_user_story.pk})
    private_url1 = reverse('userstory-voters-list', kwargs={"resource_id": data.private_user_story1.pk})
    private_url2 = reverse('userstory-voters-list', kwargs={"resource_id": data.private_user_story2.pk})
    blocked_url = reverse('userstory-voters-list', kwargs={"resource_id": data.blocked_user_story.pk})

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


def test_user_story_voters_retrieve(client, data):
    add_vote(data.public_user_story, data.project_owner)
    public_url = reverse('userstory-voters-detail', kwargs={"resource_id": data.public_user_story.pk,
                                                            "pk": data.project_owner.pk})
    add_vote(data.private_user_story1, data.project_owner)
    private_url1 = reverse('userstory-voters-detail', kwargs={"resource_id": data.private_user_story1.pk,
                                                              "pk": data.project_owner.pk})
    add_vote(data.private_user_story2, data.project_owner)
    private_url2 = reverse('userstory-voters-detail', kwargs={"resource_id": data.private_user_story2.pk,
                                                              "pk": data.project_owner.pk})

    add_vote(data.blocked_user_story, data.project_owner)
    blocked_url = reverse('userstory-voters-detail', kwargs={"resource_id": data.blocked_user_story.pk,
                                                             "pk": data.project_owner.pk})
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


def test_user_story_action_watch(client, data):
    public_url = reverse('userstories-watch', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-watch', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-watch', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-watch', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [401, 404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, "", users)
    assert results == [401, 404, 404, 451, 451]


def test_user_story_action_unwatch(client, data):
    public_url = reverse('userstories-unwatch', kwargs={"pk": data.public_user_story.pk})
    private_url1 = reverse('userstories-unwatch', kwargs={"pk": data.private_user_story1.pk})
    private_url2 = reverse('userstories-unwatch', kwargs={"pk": data.private_user_story2.pk})
    blocked_url = reverse('userstories-unwatch', kwargs={"pk": data.blocked_user_story.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, "", users)
    assert results == [401, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, "", users)
    assert results == [401, 404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, "", users)
    assert results == [401, 404, 404, 451, 451]


def test_userstory_watchers_list(client, data):
    public_url = reverse('userstory-watchers-list', kwargs={"resource_id": data.public_user_story.pk})
    private_url1 = reverse('userstory-watchers-list', kwargs={"resource_id": data.private_user_story1.pk})
    private_url2 = reverse('userstory-watchers-list', kwargs={"resource_id": data.private_user_story2.pk})
    blocked_url = reverse('userstory-watchers-list', kwargs={"resource_id": data.blocked_user_story.pk})

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


def test_userstory_watchers_retrieve(client, data):
    add_watcher(data.public_user_story, data.project_owner)
    public_url = reverse('userstory-watchers-detail', kwargs={"resource_id": data.public_user_story.pk,
                                                              "pk": data.project_owner.pk})
    add_watcher(data.private_user_story1, data.project_owner)
    private_url1 = reverse('userstory-watchers-detail', kwargs={"resource_id": data.private_user_story1.pk,
                                                                "pk": data.project_owner.pk})
    add_watcher(data.private_user_story2, data.project_owner)
    private_url2 = reverse('userstory-watchers-detail', kwargs={"resource_id": data.private_user_story2.pk,
                                                                "pk": data.project_owner.pk})
    add_watcher(data.blocked_user_story, data.project_owner)
    blocked_url = reverse('userstory-watchers-detail', kwargs={"resource_id": data.blocked_user_story.pk,
                                                               "pk": data.project_owner.pk})

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


def test_user_stories_action_csv(client, data):
    url = reverse('userstories-csv')
    csv_public_uuid = data.public_project.userstories_csv_uuid
    csv_private1_uuid = data.private_project1.userstories_csv_uuid
    csv_private2_uuid = data.private_project1.userstories_csv_uuid

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', "{}?uuid={}".format(url, csv_public_uuid), None, users)
    assert results == [200, 200, 200, 200, 200]

    results = helper_test_http_method(client, 'get', "{}?uuid={}".format(url, csv_private1_uuid), None, users)
    assert results == [200, 200, 200, 200, 200]

    results = helper_test_http_method(client, 'get', "{}?uuid={}".format(url, csv_private2_uuid), None, users)
    assert results == [200, 200, 200, 200, 200]
