import uuid

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.tasks.serializers import TaskSerializer
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS
from taiga.projects.occ import OCCResourceMixin

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

from unittest import mock

import pytest
pytestmark = pytest.mark.django_db


def setup_function(function):
    disconnect_signals()


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
                                        public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                        owner=m.project_owner,
                                        tasks_csv_uuid=uuid.uuid4().hex)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                          owner=m.project_owner,
                                          tasks_csv_uuid=uuid.uuid4().hex)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner,
                                          tasks_csv_uuid=uuid.uuid4().hex)

    m.public_membership = f.MembershipFactory(project=m.public_project,
                                              user=m.project_member_with_perms,
                                              role__project=m.public_project,
                                              role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.private_membership1 = f.MembershipFactory(project=m.private_project1,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project1,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project1,
                        user=m.project_member_without_perms,
                        role__project=m.private_project1,
                        role__permissions=[])
    m.private_membership2 = f.MembershipFactory(project=m.private_project2,
                                                user=m.project_member_with_perms,
                                                role__project=m.private_project2,
                                                role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    f.MembershipFactory(project=m.private_project2,
                        user=m.project_member_without_perms,
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

    m.public_project.default_task_status = m.public_task.status
    m.public_project.save()
    m.private_project1.default_task_status = m.private_task1.status
    m.private_project1.save()
    m.private_project2.default_task_status = m.private_task2.status
    m.private_project2.save()

    return m


def test_task_retrieve(client, data):
    public_url = reverse('tasks-detail', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-detail', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-detail', kwargs={"pk": data.private_task2.pk})

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


def test_task_update(client, data):
    public_url = reverse('tasks-detail', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-detail', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-detail', kwargs={"pk": data.private_task2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            task_data = TaskSerializer(data.public_task).data
            task_data["subject"] = "test"
            task_data = json.dumps(task_data)
            results = helper_test_http_method(client, 'put', public_url, task_data, users)
            assert results == [401, 403, 403, 200, 200]

            task_data = TaskSerializer(data.private_task1).data
            task_data["subject"] = "test"
            task_data = json.dumps(task_data)
            results = helper_test_http_method(client, 'put', private_url1, task_data, users)
            assert results == [401, 403, 403, 200, 200]

            task_data = TaskSerializer(data.private_task2).data
            task_data["subject"] = "test"
            task_data = json.dumps(task_data)
            results = helper_test_http_method(client, 'put', private_url2, task_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_task_delete(client, data):
    public_url = reverse('tasks-detail', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-detail', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-detail', kwargs={"pk": data.private_task2.pk})

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


def test_task_list(client, data):
    url = reverse('tasks-list')

    response = client.get(url)
    tasks_data = json.loads(response.content.decode('utf-8'))
    assert len(tasks_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    tasks_data = json.loads(response.content.decode('utf-8'))
    assert len(tasks_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    tasks_data = json.loads(response.content.decode('utf-8'))
    assert len(tasks_data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    tasks_data = json.loads(response.content.decode('utf-8'))
    assert len(tasks_data) == 3
    assert response.status_code == 200


def test_task_create(client, data):
    url = reverse('tasks-list')

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
        "status": data.public_project.task_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 2,
        "project": data.private_project1.pk,
        "status": data.private_project1.task_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 3,
        "project": data.private_project2.pk,
        "status": data.private_project2.task_statuses.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]


def test_task_patch(client, data):
    public_url = reverse('tasks-detail', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-detail', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-detail', kwargs={"pk": data.private_task2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            patch_data = json.dumps({"subject": "test", "version": data.public_task.version})
            results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
            assert results == [401, 403, 403, 200, 200]

            patch_data = json.dumps({"subject": "test", "version": data.private_task1.version})
            results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
            assert results == [401, 403, 403, 200, 200]

            patch_data = json.dumps({"subject": "test", "version": data.private_task2.version})
            results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_task_action_bulk_create(client, data):
    url = reverse('tasks-bulk-create')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = json.dumps({
        "bulk_tasks": "test1\ntest2",
        "us_id": data.public_task.user_story.pk,
        "project_id": data.public_task.project.pk,
        "sprint_id": data.public_task.milestone.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_tasks": "test1\ntest2",
        "us_id": data.private_task1.user_story.pk,
        "project_id": data.private_task1.project.pk,
        "sprint_id": data.private_task1.milestone.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]

    bulk_data = json.dumps({
        "bulk_tasks": "test1\ntest2",
        "us_id": data.private_task2.user_story.pk,
        "project_id": data.private_task2.project.pk,
        "sprint_id": data.private_task2.milestone.pk,
    })
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]


def test_tasks_csv(client, data):
    url = reverse('tasks-csv')
    csv_public_uuid = data.public_project.tasks_csv_uuid
    csv_private1_uuid = data.private_project1.tasks_csv_uuid
    csv_private2_uuid = data.private_project1.tasks_csv_uuid

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
