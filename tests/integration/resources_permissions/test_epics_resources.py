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
from taiga.projects.epics.serializers import EpicSerializer
from taiga.projects.epics.models import Epic
from taiga.projects.epics.utils import attach_extra_info as attach_epic_extra_info
from taiga.projects.utils import attach_extra_info as attach_project_extra_info
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.occ import OCCResourceMixin

from tests import factories as f
from tests.utils import helper_test_http_method, reconnect_signals
from taiga.projects.votes.services import add_vote
from taiga.projects.notifications.services import add_watcher

from unittest import mock

import pytest
pytestmark = pytest.mark.django_db


def setup_function(function):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()

    m.public_project = f.ProjectFactory(is_private=False,
                                        anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                        public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)) + ["comment_epic"],
                                        owner=m.project_owner,
                                        epics_csv_uuid=uuid.uuid4().hex)
    m.public_project = attach_project_extra_info(Project.objects.all()).get(id=m.public_project.id)

    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          owner=m.project_owner,
                                          epics_csv_uuid=uuid.uuid4().hex)
    m.private_project1 = attach_project_extra_info(Project.objects.all()).get(id=m.private_project1.id)

    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner,
                                          epics_csv_uuid=uuid.uuid4().hex)
    m.private_project2 = attach_project_extra_info(Project.objects.all()).get(id=m.private_project2.id)

    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         epics_csv_uuid=uuid.uuid4().hex,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF)
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
    f.MembershipFactory(
        project=m.private_project1,
        user=m.project_member_without_perms,
        role__project=m.private_project1,
        role__permissions=[])
    m.private_membership2 = f.MembershipFactory(
        project=m.private_project2,
        user=m.project_member_with_perms,
        role__project=m.private_project2,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(
        project=m.private_project2,
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

    m.public_epic = f.EpicFactory(project=m.public_project,
                                  status__project=m.public_project)
    m.public_epic = attach_epic_extra_info(Epic.objects.all()).get(id=m.public_epic.id)

    m.private_epic1 = f.EpicFactory(project=m.private_project1,
                                    status__project=m.private_project1)
    m.private_epic1 = attach_epic_extra_info(Epic.objects.all()).get(id=m.private_epic1.id)

    m.private_epic2 = f.EpicFactory(project=m.private_project2,
                                    status__project=m.private_project2)
    m.private_epic2 = attach_epic_extra_info(Epic.objects.all()).get(id=m.private_epic2.id)

    m.blocked_epic = f.EpicFactory(project=m.blocked_project,
                                   status__project=m.blocked_project)
    m.blocked_epic = attach_epic_extra_info(Epic.objects.all()).get(id=m.blocked_epic.id)


    m.public_us = f.UserStoryFactory(project=m.public_project)
    m.private_us1 = f.UserStoryFactory(project=m.private_project1)
    m.private_us2 = f.UserStoryFactory(project=m.private_project2)
    m.blocked_us = f.UserStoryFactory(project=m.blocked_project)

    m.public_related_us = f.RelatedUserStory(epic=m.public_epic, user_story=m.public_us)
    m.private_related_us1 = f.RelatedUserStory(epic=m.private_epic1, user_story=m.private_us1)
    m.private_related_us2 = f.RelatedUserStory(epic=m.private_epic2, user_story=m.private_us2)
    m.blocked_related_us = f.RelatedUserStory(epic=m.blocked_epic, user_story=m.blocked_us)

    m.public_project.default_epic_status = m.public_epic.status
    m.public_project.save()
    m.private_project1.default_epic_status = m.private_epic1.status
    m.private_project1.save()
    m.private_project2.default_epic_status = m.private_epic2.status
    m.private_project2.save()
    m.blocked_project.default_epic_status = m.blocked_epic.status
    m.blocked_project.save()

    return m


def test_epic_list(client, data):
    url = reverse('epics-list')

    response = client.get(url)
    epics_data = json.loads(response.content.decode('utf-8'))
    assert len(epics_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    epics_data = json.loads(response.content.decode('utf-8'))
    assert len(epics_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    epics_data = json.loads(response.content.decode('utf-8'))
    assert len(epics_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    epics_data = json.loads(response.content.decode('utf-8'))
    assert len(epics_data) == 4
    assert response.status_code == 200


def test_epic_retrieve(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_create(client, data):
    url = reverse('epics-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({
        "subject": "test",
        "ref": 1,
        "project": data.public_project.pk,
        "status": data.public_project.epic_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 2,
        "project": data.private_project1.pk,
        "status": data.private_project1.epic_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 3,
        "project": data.private_project2.pk,
        "status": data.private_project2.epic_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 3,
        "project": data.blocked_project.pk,
        "status": data.blocked_project.epic_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_epic_put_update(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        epic_data = EpicSerializer(data.public_epic).data
        epic_data["subject"] = "test"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', public_url, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic1).data
        epic_data["subject"] = "test"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url1, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic2).data
        epic_data["subject"] = "test"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url2, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.blocked_epic).data
        epic_data["subject"] = "test"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', blocked_url, epic_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_put_comment(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        epic_data = EpicSerializer(data.public_epic).data
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', public_url, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic1).data
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url1, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic2).data
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url2, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.blocked_epic).data
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', blocked_url, epic_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_put_update_and_comment(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        epic_data = EpicSerializer(data.public_epic).data
        epic_data["subject"] = "test"
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', public_url, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic1).data
        epic_data["subject"] = "test"
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url1, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.private_epic2).data
        epic_data["subject"] = "test"
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', private_url2, epic_data, users)
        assert results == [401, 403, 403, 200, 200]

        epic_data = EpicSerializer(data.blocked_epic).data
        epic_data["subject"] = "test"
        epic_data["comment"] = "test comment"
        epic_data = json.dumps(epic_data)
        results = helper_test_http_method(client, 'put', blocked_url, epic_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_put_update_with_project_change(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    user3 = f.UserFactory.create()
    user4 = f.UserFactory.create()
    project1 = f.ProjectFactory()
    project2 = f.ProjectFactory()

    epic_status1 = f.EpicStatusFactory.create(project=project1)
    epic_status2 = f.EpicStatusFactory.create(project=project2)

    project1.default_epic_status = epic_status1
    project2.default_epic_status = epic_status2

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

    epic = f.EpicFactory.create(project=project1)
    epic = attach_epic_extra_info(Epic.objects.all()).get(id=epic.id)

    url = reverse('epics-detail', kwargs={"pk": epic.pk})

    # Test user with permissions in both projects
    client.login(user1)

    epic_data = EpicSerializer(epic).data
    epic_data["project"] = project2.id
    epic_data = json.dumps(epic_data)

    response = client.put(url, data=epic_data, content_type="application/json")

    assert response.status_code == 200

    epic.project = project1
    epic.save()

    # Test user with permissions in only origin project
    client.login(user2)

    epic_data = EpicSerializer(epic).data
    epic_data["project"] = project2.id
    epic_data = json.dumps(epic_data)

    response = client.put(url, data=epic_data, content_type="application/json")

    assert response.status_code == 403

    epic.project = project1
    epic.save()

    # Test user with permissions in only destionation project
    client.login(user3)

    epic_data = EpicSerializer(epic).data
    epic_data["project"] = project2.id
    epic_data = json.dumps(epic_data)

    response = client.put(url, data=epic_data, content_type="application/json")

    assert response.status_code == 403

    epic.project = project1
    epic.save()

    # Test user without permissions in the projects
    client.login(user4)

    epic_data = EpicSerializer(epic).data
    epic_data["project"] = project2.id
    epic_data = json.dumps(epic_data)

    response = client.put(url, data=epic_data, content_type="application/json")

    assert response.status_code == 403

    epic.project = project1
    epic.save()


def test_epic_patch_update(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        patch_data = json.dumps({"subject": "test", "version": data.public_epic.version})
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.private_epic1.version})
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.private_epic2.version})
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"subject": "test", "version": data.blocked_epic.version})
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_patch_comment(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        patch_data = json.dumps({"comment": "test comment", "version": data.public_epic.version})
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 200, 200, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.private_epic1.version})
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.private_epic2.version})
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({"comment": "test comment", "version": data.blocked_epic.version})
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_patch_update_and_comment(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

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
            "version": data.public_epic.version
        })
        results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.private_epic1.version
        })
        results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.private_epic2.version
        })
        results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
        assert results == [401, 403, 403, 200, 200]

        patch_data = json.dumps({
            "subject": "test",
            "comment": "test comment",
            "version": data.blocked_epic.version
        })
        results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
        assert results == [401, 403, 403, 451, 451]


def test_epic_delete(client, data):
    public_url = reverse('epics-detail', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-detail', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-detail', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-detail', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_action_bulk_create(client, data):
    url = reverse('epics-bulk-create')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = json.dumps({
        "bulk_epics": "test1\ntest2",
        "project_id": data.public_epic.project.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_epics": "test1\ntest2",
        "project_id": data.private_epic1.project.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_epics": "test1\ntest2",
        "project_id": data.private_epic2.project.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_epics": "test1\ntest2",
        "project_id": data.blocked_epic.project.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_epic_action_upvote(client, data):
    public_url = reverse('epics-upvote', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-upvote', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-upvote', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-upvote', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_action_downvote(client, data):
    public_url = reverse('epics-downvote', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-downvote', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-downvote', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-downvote', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_voters_list(client, data):
    public_url = reverse('epic-voters-list', kwargs={"resource_id": data.public_epic.pk})
    private_url1 = reverse('epic-voters-list', kwargs={"resource_id": data.private_epic1.pk})
    private_url2 = reverse('epic-voters-list', kwargs={"resource_id": data.private_epic2.pk})
    blocked_url = reverse('epic-voters-list', kwargs={"resource_id": data.blocked_epic.pk})

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


def test_epic_voters_retrieve(client, data):
    add_vote(data.public_epic, data.project_owner)
    public_url = reverse('epic-voters-detail', kwargs={"resource_id": data.public_epic.pk,
                                                       "pk": data.project_owner.pk})
    add_vote(data.private_epic1, data.project_owner)
    private_url1 = reverse('epic-voters-detail', kwargs={"resource_id": data.private_epic1.pk,
                                                         "pk": data.project_owner.pk})
    add_vote(data.private_epic2, data.project_owner)
    private_url2 = reverse('epic-voters-detail', kwargs={"resource_id": data.private_epic2.pk,
                                                         "pk": data.project_owner.pk})

    add_vote(data.blocked_epic, data.project_owner)
    blocked_url = reverse('epic-voters-detail', kwargs={"resource_id": data.blocked_epic.pk,
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


def test_epic_action_watch(client, data):
    public_url = reverse('epics-watch', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-watch', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-watch', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-watch', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_action_unwatch(client, data):
    public_url = reverse('epics-unwatch', kwargs={"pk": data.public_epic.pk})
    private_url1 = reverse('epics-unwatch', kwargs={"pk": data.private_epic1.pk})
    private_url2 = reverse('epics-unwatch', kwargs={"pk": data.private_epic2.pk})
    blocked_url = reverse('epics-unwatch', kwargs={"pk": data.blocked_epic.pk})

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


def test_epic_watchers_list(client, data):
    public_url = reverse('epic-watchers-list', kwargs={"resource_id": data.public_epic.pk})
    private_url1 = reverse('epic-watchers-list', kwargs={"resource_id": data.private_epic1.pk})
    private_url2 = reverse('epic-watchers-list', kwargs={"resource_id": data.private_epic2.pk})
    blocked_url = reverse('epic-watchers-list', kwargs={"resource_id": data.blocked_epic.pk})

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


def test_epic_watchers_retrieve(client, data):
    add_watcher(data.public_epic, data.project_owner)
    public_url = reverse('epic-watchers-detail', kwargs={"resource_id": data.public_epic.pk,
                                                         "pk": data.project_owner.pk})
    add_watcher(data.private_epic1, data.project_owner)
    private_url1 = reverse('epic-watchers-detail', kwargs={"resource_id": data.private_epic1.pk,
                                                           "pk": data.project_owner.pk})
    add_watcher(data.private_epic2, data.project_owner)
    private_url2 = reverse('epic-watchers-detail', kwargs={"resource_id": data.private_epic2.pk,
                                                           "pk": data.project_owner.pk})

    add_watcher(data.blocked_epic, data.project_owner)
    blocked_url = reverse('epic-watchers-detail', kwargs={"resource_id": data.blocked_epic.pk,
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


def test_epics_csv(client, data):
    url = reverse('epics-csv')
    csv_public_uuid = data.public_project.epics_csv_uuid
    csv_private1_uuid = data.private_project1.epics_csv_uuid
    csv_private2_uuid = data.private_project1.epics_csv_uuid
    csv_blocked_uuid = data.blocked_project.epics_csv_uuid

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

    results = helper_test_http_method(client, 'get', "{}?uuid={}".format(url, csv_blocked_uuid), None, users)
    assert results == [200, 200, 200, 200, 200]
