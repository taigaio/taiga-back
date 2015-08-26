import uuid

from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects.tasks.serializers import TaskSerializer
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS
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

    milestone_public_task = f.MilestoneFactory(project=m.public_project)
    milestone_private_task1 = f.MilestoneFactory(project=m.private_project1)
    milestone_private_task2 = f.MilestoneFactory(project=m.private_project2)

    m.public_task = f.TaskFactory(project=m.public_project,
                                  status__project=m.public_project,
                                  milestone=milestone_public_task,
                                  user_story__project=m.public_project,
                                  user_story__milestone=milestone_public_task)
    m.private_task1 = f.TaskFactory(project=m.private_project1,
                                    status__project=m.private_project1,
                                    milestone=milestone_private_task1,
                                    user_story__project=m.private_project1,
                                    user_story__milestone=milestone_private_task1)
    m.private_task2 = f.TaskFactory(project=m.private_project2,
                                    status__project=m.private_project2,
                                    milestone=milestone_private_task2,
                                    user_story__project=m.private_project2,
                                    user_story__milestone=milestone_private_task2)

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


def test_task_update_with_project_change(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    user3 = f.UserFactory.create()
    user4 = f.UserFactory.create()
    project1 = f.ProjectFactory()
    project2 = f.ProjectFactory()

    task_status1 = f.TaskStatusFactory.create(project=project1)
    task_status2 = f.TaskStatusFactory.create(project=project2)

    project1.default_task_status = task_status1
    project2.default_task_status = task_status2

    project1.save()
    project2.save()

    membership1 = f.MembershipFactory(project=project1,
                                      user=user1,
                                      role__project=project1,
                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    membership2 = f.MembershipFactory(project=project2,
                                      user=user1,
                                      role__project=project2,
                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    membership3 = f.MembershipFactory(project=project1,
                                      user=user2,
                                      role__project=project1,
                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    membership4 = f.MembershipFactory(project=project2,
                                      user=user3,
                                      role__project=project2,
                                      role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))

    task = f.TaskFactory.create(project=project1)

    url = reverse('tasks-detail', kwargs={"pk": task.pk})

    # Test user with permissions in both projects
    client.login(user1)

    task_data = TaskSerializer(task).data
    task_data["project"] = project2.id
    task_data = json.dumps(task_data)

    response = client.put(url, data=task_data, content_type="application/json")

    assert response.status_code == 200

    task.project = project1
    task.save()

    # Test user with permissions in only origin project
    client.login(user2)

    task_data = TaskSerializer(task).data
    task_data["project"] = project2.id
    task_data = json.dumps(task_data)

    response = client.put(url, data=task_data, content_type="application/json")

    assert response.status_code == 403

    task.project = project1
    task.save()

    # Test user with permissions in only destionation project
    client.login(user3)

    task_data = TaskSerializer(task).data
    task_data["project"] = project2.id
    task_data = json.dumps(task_data)

    response = client.put(url, data=task_data, content_type="application/json")

    assert response.status_code == 403

    task.project = project1
    task.save()

    # Test user without permissions in the projects
    client.login(user4)

    task_data = TaskSerializer(task).data
    task_data["project"] = project2.id
    task_data = json.dumps(task_data)

    response = client.put(url, data=task_data, content_type="application/json")

    assert response.status_code == 403

    task.project = project1
    task.save()


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


def test_task_action_upvote(client, data):
    public_url = reverse('tasks-upvote', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-upvote', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-upvote', kwargs={"pk": data.private_task2.pk})

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
    assert results == [404, 404, 404, 200, 200]


def test_task_action_downvote(client, data):
    public_url = reverse('tasks-downvote', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-downvote', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-downvote', kwargs={"pk": data.private_task2.pk})

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
    assert results == [404, 404, 404, 200, 200]


def test_task_voters_list(client, data):
    public_url = reverse('task-voters-list', kwargs={"resource_id": data.public_task.pk})
    private_url1 = reverse('task-voters-list', kwargs={"resource_id": data.private_task1.pk})
    private_url2 = reverse('task-voters-list', kwargs={"resource_id": data.private_task2.pk})

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


def test_task_voters_retrieve(client, data):
    add_vote(data.public_task, data.project_owner)
    public_url = reverse('task-voters-detail', kwargs={"resource_id": data.public_task.pk,
                                                        "pk": data.project_owner.pk})
    add_vote(data.private_task1, data.project_owner)
    private_url1 = reverse('task-voters-detail', kwargs={"resource_id": data.private_task1.pk,
                                                          "pk": data.project_owner.pk})
    add_vote(data.private_task2, data.project_owner)
    private_url2 = reverse('task-voters-detail', kwargs={"resource_id": data.private_task2.pk,
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


def test_task_action_watch(client, data):
    public_url = reverse('tasks-watch', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-watch', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-watch', kwargs={"pk": data.private_task2.pk})

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
    assert results == [404, 404, 404, 200, 200]


def test_task_action_unwatch(client, data):
    public_url = reverse('tasks-unwatch', kwargs={"pk": data.public_task.pk})
    private_url1 = reverse('tasks-unwatch', kwargs={"pk": data.private_task1.pk})
    private_url2 = reverse('tasks-unwatch', kwargs={"pk": data.private_task2.pk})

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
    assert results == [404, 404, 404, 200, 200]


def test_task_watchers_list(client, data):
    public_url = reverse('task-watchers-list', kwargs={"resource_id": data.public_task.pk})
    private_url1 = reverse('task-watchers-list', kwargs={"resource_id": data.private_task1.pk})
    private_url2 = reverse('task-watchers-list', kwargs={"resource_id": data.private_task2.pk})

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


def test_task_watchers_retrieve(client, data):
    add_watcher(data.public_task, data.project_owner)
    public_url = reverse('task-watchers-detail', kwargs={"resource_id": data.public_task.pk,
                                                            "pk": data.project_owner.pk})
    add_watcher(data.private_task1, data.project_owner)
    private_url1 = reverse('task-watchers-detail', kwargs={"resource_id": data.private_task1.pk,
                                                              "pk": data.project_owner.pk})
    add_watcher(data.private_task2, data.project_owner)
    private_url2 = reverse('task-watchers-detail', kwargs={"resource_id": data.private_task2.pk,
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
