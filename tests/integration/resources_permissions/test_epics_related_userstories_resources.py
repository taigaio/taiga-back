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
from taiga.projects.epics.serializers import EpicRelatedUserStorySerializer
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
                                        public_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
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


def test_epic_related_userstories_list(client, data):
    url = reverse('epics-related-userstories-list', args=[data.public_epic.pk])
    response = client.get(url)
    related_uss_data = json.loads(response.content.decode('utf-8'))
    assert len(related_uss_data) == 1
    assert response.status_code == 200

    url = reverse('epics-related-userstories-list', args=[data.private_epic2.pk])
    response = client.get(url)
    assert response.status_code == 401

    client.login(data.registered_user)

    url = reverse('epics-related-userstories-list', args=[data.private_epic1.pk])
    response = client.get(url)
    related_uss_data = json.loads(response.content.decode('utf-8'))
    assert len(related_uss_data) == 1
    assert response.status_code == 200

    url = reverse('epics-related-userstories-list', args=[data.private_epic2.pk])
    response = client.get(url)
    assert response.status_code == 403

    client.login(data.project_member_with_perms)

    url = reverse('epics-related-userstories-list', args=[data.private_epic2.pk])
    response = client.get(url)
    related_uss_data = json.loads(response.content.decode('utf-8'))
    assert len(related_uss_data) == 1
    assert response.status_code == 200

    client.login(data.project_owner)

    url = reverse('epics-related-userstories-list', args=[data.blocked_epic.pk])
    response = client.get(url)
    related_uss_data = json.loads(response.content.decode('utf-8'))
    assert len(related_uss_data) == 1
    assert response.status_code == 200


def test_epic_related_userstories_retrieve(client, data):
    public_url = reverse('epics-related-userstories-detail', args=[data.public_epic.pk, data.public_us.pk])
    private_url1 = reverse('epics-related-userstories-detail', args=[data.private_epic1.pk, data.private_us1.pk])
    private_url2 = reverse('epics-related-userstories-detail', args=[data.private_epic2.pk, data.private_us2.pk])
    blocked_url = reverse('epics-related-userstories-detail', args=[data.blocked_epic.pk, data.blocked_us.pk])

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


def test_epic_related_userstories_create(client, data):
    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    create_data = json.dumps({
        "user_story": f.UserStoryFactory(project=data.public_project).id,
        "epic": str(data.public_epic.id)
    })
    url = reverse('epics-related-userstories-list', args=[data.public_epic.pk])
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 400]

    create_data = json.dumps({
        "user_story": f.UserStoryFactory(project=data.private_project1).id,
        "epic": data.private_epic1.id
    })
    url = reverse('epics-related-userstories-list', args=[data.private_epic1.pk])
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 400]

    create_data = json.dumps({
        "user_story": f.UserStoryFactory(project=data.private_project2).id,
        "epic": data.private_epic2.id
    })
    url = reverse('epics-related-userstories-list', args=[data.private_epic2.pk])
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 400]

    create_data = json.dumps({
        "user_story": f.UserStoryFactory(project=data.blocked_project).id,
        "epic": data.blocked_epic.id
    })
    url = reverse('epics-related-userstories-list', args=[data.blocked_epic.pk])
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_epic_related_userstories_create_rejects_mismatched_epic(client, data):
    client.login(data.project_member_with_perms)
    story = f.UserStoryFactory(project=data.private_project2)
    url = reverse('epics-related-userstories-list', args=[data.private_epic1.pk])
    body = json.dumps({"user_story": story.pk, "epic": str(data.private_epic2.pk)})

    response = client.post(url, body, content_type='application/json')

    assert response.status_code == 400
    assert not data.private_epic1.relateduserstory_set.filter(user_story=story).exists()
    assert not data.private_epic2.relateduserstory_set.filter(user_story=story).exists()


def test_epic_related_userstories_create_checks_url_epic_permission_first(client, data):
    user = f.UserFactory()
    f.MembershipFactory(
        project=data.public_project,
        user=user,
        role__project=data.public_project,
        role__permissions=['modify_epic'])
    story = f.UserStoryFactory(project=data.public_project)
    client.login(user)
    url = reverse('epics-related-userstories-list', args=[data.private_epic2.pk])
    body = json.dumps({"user_story": story.pk, "epic": data.public_epic.pk})

    response = client.post(url, body, content_type='application/json')

    assert response.status_code == 403
    assert not data.private_epic2.relateduserstory_set.filter(user_story=story).exists()
    assert not data.public_epic.relateduserstory_set.filter(user_story=story).exists()


def test_epic_related_userstories_put_update(client, data):
    public_url = reverse('epics-related-userstories-detail', args=[data.public_epic.pk, data.public_us.pk])
    private_url1 = reverse('epics-related-userstories-detail', args=[data.private_epic1.pk, data.private_us1.pk])
    private_url2 = reverse('epics-related-userstories-detail', args=[data.private_epic2.pk, data.private_us2.pk])
    blocked_url = reverse('epics-related-userstories-detail', args=[data.blocked_epic.pk, data.blocked_us.pk])

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    epic_related_us_data = EpicRelatedUserStorySerializer(data.public_related_us).data
    epic_related_us_data["order"] = 33
    epic_related_us_data = json.dumps(epic_related_us_data)
    results = helper_test_http_method(client, 'put', public_url, epic_related_us_data, users)
    assert results == [401, 403, 403, 200, 200]

    epic_related_us_data = EpicRelatedUserStorySerializer(data.private_related_us1).data
    epic_related_us_data["order"] = 33
    epic_related_us_data = json.dumps(epic_related_us_data)
    results = helper_test_http_method(client, 'put', private_url1, epic_related_us_data, users)
    assert results == [401, 403, 403, 200, 200]

    epic_related_us_data = EpicRelatedUserStorySerializer(data.private_related_us2).data
    epic_related_us_data["order"] = 33
    epic_related_us_data = json.dumps(epic_related_us_data)
    results = helper_test_http_method(client, 'put', private_url2, epic_related_us_data, users)
    assert results == [401, 403, 403, 200, 200]

    epic_related_us_data = EpicRelatedUserStorySerializer(data.blocked_related_us).data
    epic_related_us_data["order"] = 33
    epic_related_us_data = json.dumps(epic_related_us_data)
    results = helper_test_http_method(client, 'put', blocked_url, epic_related_us_data, users)
    assert results == [401, 403, 403, 451, 451]


def test_epic_related_userstories_patch_update(client, data):
    public_url = reverse('epics-related-userstories-detail', args=[data.public_epic.pk, data.public_us.pk])
    private_url1 = reverse('epics-related-userstories-detail', args=[data.private_epic1.pk, data.private_us1.pk])
    private_url2 = reverse('epics-related-userstories-detail', args=[data.private_epic2.pk, data.private_us2.pk])
    blocked_url = reverse('epics-related-userstories-detail', args=[data.blocked_epic.pk, data.blocked_us.pk])

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    patch_data = json.dumps({"order": 33})

    results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
    assert results == [401, 403, 403, 200, 200]

    results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
    assert results == [401, 403, 403, 451, 451]


@pytest.mark.parametrize("method", ["put", "patch"])
def test_epic_related_userstory_update_rejects_epic_change(client, data, method):
    user = f.UserFactory()
    f.MembershipFactory(
        project=data.private_project1,
        user=user,
        role__project=data.private_project1,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    client.login(user)

    related_us = data.private_related_us1
    original_order = related_us.order
    body = EpicRelatedUserStorySerializer(related_us).data if method == "put" else {}
    body.update({"epic": data.private_epic2.pk})
    url = reverse('epics-related-userstories-detail', args=[data.private_epic1.pk, data.private_us1.pk])
    response = getattr(client, method)(url, json.dumps(body), content_type='application/json')

    assert response.status_code == 400
    related_us.refresh_from_db()
    assert related_us.epic_id == data.private_epic1.pk
    assert related_us.user_story_id == data.private_us1.pk
    assert related_us.order == original_order
    assert not data.private_epic2.relateduserstory_set.filter(user_story=data.private_us1).exists()


def test_epic_related_userstories_delete(client, data):
    public_url = reverse('epics-related-userstories-detail', args=[data.public_epic.pk, data.public_us.pk])
    private_url1 = reverse('epics-related-userstories-detail', args=[data.private_epic1.pk, data.private_us1.pk])
    private_url2 = reverse('epics-related-userstories-detail', args=[data.private_epic2.pk, data.private_us2.pk])
    blocked_url = reverse('epics-related-userstories-detail', args=[data.blocked_epic.pk, data.blocked_us.pk])

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


def test_bulk_create_related_userstories(client, data):
    public_url = reverse('epics-related-userstories-bulk-create', args=[data.public_epic.pk])
    private_url1 = reverse('epics-related-userstories-bulk-create', args=[data.private_epic1.pk])
    private_url2 = reverse('epics-related-userstories-bulk-create', args=[data.private_epic2.pk])
    blocked_url = reverse('epics-related-userstories-bulk-create', args=[data.blocked_epic.pk])

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = json.dumps({
        "bulk_userstories": "test1\ntest2",
        "project_id": data.public_project.id
    })
    results = helper_test_http_method(client, 'post', public_url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_userstories": "test1\ntest2",
        "project_id": data.private_project1.id
    })
    results = helper_test_http_method(client, 'post', private_url1, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_userstories": "test1\ntest2",
        "project_id": data.private_project2.id
    })
    results = helper_test_http_method(client, 'post', private_url2, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_userstories": "test1\ntest2",
        "project_id": data.blocked_project.id
    })
    results = helper_test_http_method(client, 'post', blocked_url, bulk_data, users)
    assert results == [401, 403, 403, 451, 451]


@pytest.mark.parametrize("authorized_side", ["epic", "stories"])
def test_bulk_create_requires_permissions_on_epic_and_story_project(client, data, authorized_side):
    user = f.UserFactory()
    authorized_project = data.private_project1 if authorized_side == "epic" else data.private_project2
    f.MembershipFactory(
        project=authorized_project,
        user=user,
        role__project=authorized_project,
        role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    client.login(user)
    url = reverse('epics-related-userstories-bulk-create', args=[data.private_epic1.pk])
    body = json.dumps({"bulk_userstories": "cross-project story", "project_id": data.private_project2.pk})
    story_count = data.private_project2.user_stories.count()
    relation_count = data.private_epic1.relateduserstory_set.count()

    response = client.post(url, body, content_type='application/json')

    assert response.status_code == 403
    assert data.private_project2.user_stories.count() == story_count
    assert data.private_epic1.relateduserstory_set.count() == relation_count


def test_bulk_create_related_userstories_cross_project(client, data):
    client.login(data.project_member_with_perms)
    url = reverse('epics-related-userstories-bulk-create', args=[data.private_epic1.pk])
    body = json.dumps({"bulk_userstories": "cross-project story", "project_id": data.private_project2.pk})
    existing_relations = set(data.private_epic1.relateduserstory_set.values_list('pk', flat=True))

    response = client.post(url, body, content_type='application/json')

    assert response.status_code == 200
    story = data.private_project2.user_stories.get(subject="cross-project story")
    relation = data.private_epic1.relateduserstory_set.get(user_story=story)
    assert relation.user_story.project_id == data.private_project2.pk
    assert existing_relations <= set(data.private_epic1.relateduserstory_set.values_list('pk', flat=True))


@pytest.mark.parametrize(
    "epic_fixture, project_fixture, expected_status",
    [("blocked_epic", "blocked_project", 451), ("private_epic1", "private_project1", 403)])
def test_bulk_create_rejects_blocked_or_archived_epic(client, data, epic_fixture, project_fixture, expected_status):
    epic = getattr(data, epic_fixture)
    project = getattr(data, project_fixture)
    if project_fixture == "private_project1":
        project.archived_code = "test"
        project.save(update_fields=["archived_code"])
    client.login(data.project_member_with_perms)
    url = reverse('epics-related-userstories-bulk-create', args=[epic.pk])
    body = json.dumps({"bulk_userstories": "disallowed epic story", "project_id": data.public_project.pk})
    story_count = data.public_project.user_stories.count()
    relation_count = epic.relateduserstory_set.count()

    response = client.post(url, body, content_type='application/json')

    assert response.status_code == expected_status
    assert data.public_project.user_stories.count() == story_count
    assert epic.relateduserstory_set.count() == relation_count
