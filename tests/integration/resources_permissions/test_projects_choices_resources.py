from django.core.urlresolvers import reverse

from taiga.base.utils import json
from taiga.projects import choices as project_choices
from taiga.projects import serializers
from taiga.users.serializers import RoleSerializer
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

    m.public_points = f.PointsFactory(project=m.public_project)
    m.private_points1 = f.PointsFactory(project=m.private_project1)
    m.private_points2 = f.PointsFactory(project=m.private_project2)
    m.blocked_points = f.PointsFactory(project=m.blocked_project)

    m.public_user_story_status = f.UserStoryStatusFactory(project=m.public_project)
    m.private_user_story_status1 = f.UserStoryStatusFactory(project=m.private_project1)
    m.private_user_story_status2 = f.UserStoryStatusFactory(project=m.private_project2)
    m.blocked_user_story_status = f.UserStoryStatusFactory(project=m.blocked_project)

    m.public_task_status = f.TaskStatusFactory(project=m.public_project)
    m.private_task_status1 = f.TaskStatusFactory(project=m.private_project1)
    m.private_task_status2 = f.TaskStatusFactory(project=m.private_project2)
    m.blocked_task_status = f.TaskStatusFactory(project=m.blocked_project)

    m.public_issue_status = f.IssueStatusFactory(project=m.public_project)
    m.private_issue_status1 = f.IssueStatusFactory(project=m.private_project1)
    m.private_issue_status2 = f.IssueStatusFactory(project=m.private_project2)
    m.blocked_issue_status = f.IssueStatusFactory(project=m.blocked_project)

    m.public_issue_type = f.IssueTypeFactory(project=m.public_project)
    m.private_issue_type1 = f.IssueTypeFactory(project=m.private_project1)
    m.private_issue_type2 = f.IssueTypeFactory(project=m.private_project2)
    m.blocked_issue_type = f.IssueTypeFactory(project=m.blocked_project)

    m.public_priority = f.PriorityFactory(project=m.public_project)
    m.private_priority1 = f.PriorityFactory(project=m.private_project1)
    m.private_priority2 = f.PriorityFactory(project=m.private_project2)
    m.blocked_priority = f.PriorityFactory(project=m.blocked_project)

    m.public_severity = f.SeverityFactory(project=m.public_project)
    m.private_severity1 = f.SeverityFactory(project=m.private_project1)
    m.private_severity2 = f.SeverityFactory(project=m.private_project2)
    m.blocked_severity = f.SeverityFactory(project=m.blocked_project)

    m.project_template = m.public_project.creation_template

    return m


def test_roles_retrieve(client, data):
    public_url = reverse('roles-detail', kwargs={"pk": data.public_project.roles.all()[0].pk})
    private1_url = reverse('roles-detail', kwargs={"pk": data.private_project1.roles.all()[0].pk})
    private2_url = reverse('roles-detail', kwargs={"pk": data.private_project2.roles.all()[0].pk})
    blocked_url = reverse('roles-detail', kwargs={"pk": data.blocked_project.roles.all()[0].pk})

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


def test_roles_update(client, data):
    public_url = reverse('roles-detail', kwargs={"pk": data.public_project.roles.all()[0].pk})
    private1_url = reverse('roles-detail', kwargs={"pk": data.private_project1.roles.all()[0].pk})
    private2_url = reverse('roles-detail', kwargs={"pk": data.private_project2.roles.all()[0].pk})
    blocked_url = reverse('roles-detail', kwargs={"pk": data.blocked_project.roles.all()[0].pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    role_data = RoleSerializer(data.public_project.roles.all()[0]).data
    role_data["name"] = "test"
    role_data = json.dumps(role_data)
    results = helper_test_http_method(client, 'put', public_url, role_data, users)
    assert results == [401, 403, 403, 403, 200]

    role_data = RoleSerializer(data.private_project1.roles.all()[0]).data
    role_data["name"] = "test"
    role_data = json.dumps(role_data)
    results = helper_test_http_method(client, 'put', private1_url, role_data, users)
    assert results == [401, 403, 403, 403, 200]

    role_data = RoleSerializer(data.private_project2.roles.all()[0]).data
    role_data["name"] = "test"
    role_data = json.dumps(role_data)
    results = helper_test_http_method(client, 'put', private2_url, role_data, users)
    assert results == [401, 403, 403, 403, 200]

    role_data = RoleSerializer(data.blocked_project.roles.all()[0]).data
    role_data["name"] = "test"
    role_data = json.dumps(role_data)
    results = helper_test_http_method(client, 'put', blocked_url, role_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_roles_delete(client, data):
    public_url = reverse('roles-detail', kwargs={"pk": data.public_project.roles.all()[0].pk})
    private1_url = reverse('roles-detail', kwargs={"pk": data.private_project1.roles.all()[0].pk})
    private2_url = reverse('roles-detail', kwargs={"pk": data.private_project2.roles.all()[0].pk})
    blocked_url = reverse('roles-detail', kwargs={"pk": data.blocked_project.roles.all()[0].pk})

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


def test_roles_list(client, data):
    url = reverse('roles-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 3
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 3
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 3
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 7
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 7
    assert response.status_code == 200


def test_roles_patch(client, data):
    public_url = reverse('roles-detail', kwargs={"pk": data.public_project.roles.all()[0].pk})
    private1_url = reverse('roles-detail', kwargs={"pk": data.private_project1.roles.all()[0].pk})
    private2_url = reverse('roles-detail', kwargs={"pk": data.private_project2.roles.all()[0].pk})
    blocked_url = reverse('roles-detail', kwargs={"pk": data.blocked_project.roles.all()[0].pk})

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


def test_points_retrieve(client, data):
    public_url = reverse('points-detail', kwargs={"pk": data.public_points.pk})
    private1_url = reverse('points-detail', kwargs={"pk": data.private_points1.pk})
    private2_url = reverse('points-detail', kwargs={"pk": data.private_points2.pk})
    blocked_url = reverse('points-detail', kwargs={"pk": data.blocked_points.pk})

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


def test_points_update(client, data):
    public_url = reverse('points-detail', kwargs={"pk": data.public_points.pk})
    private1_url = reverse('points-detail', kwargs={"pk": data.private_points1.pk})
    private2_url = reverse('points-detail', kwargs={"pk": data.private_points2.pk})
    blocked_url = reverse('points-detail', kwargs={"pk": data.blocked_points.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    points_data = serializers.PointsSerializer(data.public_points).data
    points_data["name"] = "test"
    points_data = json.dumps(points_data)
    results = helper_test_http_method(client, 'put', public_url, points_data, users)
    assert results == [401, 403, 403, 403, 200]

    points_data = serializers.PointsSerializer(data.private_points1).data
    points_data["name"] = "test"
    points_data = json.dumps(points_data)
    results = helper_test_http_method(client, 'put', private1_url, points_data, users)
    assert results == [401, 403, 403, 403, 200]

    points_data = serializers.PointsSerializer(data.private_points2).data
    points_data["name"] = "test"
    points_data = json.dumps(points_data)
    results = helper_test_http_method(client, 'put', private2_url, points_data, users)
    assert results == [401, 403, 403, 403, 200]

    points_data = serializers.PointsSerializer(data.blocked_points).data
    points_data["name"] = "test"
    points_data = json.dumps(points_data)
    results = helper_test_http_method(client, 'put', blocked_url, points_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_points_delete(client, data):
    public_url = reverse('points-detail', kwargs={"pk": data.public_points.pk})
    private1_url = reverse('points-detail', kwargs={"pk": data.private_points1.pk})
    private2_url = reverse('points-detail', kwargs={"pk": data.private_points2.pk})
    blocked_url = reverse('points-detail', kwargs={"pk": data.blocked_points.pk})

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


def test_points_list(client, data):
    url = reverse('points-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_points_patch(client, data):
    public_url = reverse('points-detail', kwargs={"pk": data.public_points.pk})
    private1_url = reverse('points-detail', kwargs={"pk": data.private_points1.pk})
    private2_url = reverse('points-detail', kwargs={"pk": data.private_points2.pk})
    blocked_url = reverse('points-detail', kwargs={"pk": data.blocked_points.pk})

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


def test_points_action_bulk_update_order(client, data):
    url = reverse('points-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_points": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_points": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_points": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_points": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_user_story_status_retrieve(client, data):
    public_url = reverse('userstory-statuses-detail', kwargs={"pk": data.public_user_story_status.pk})
    private1_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status1.pk})
    private2_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status2.pk})
    blocked_url = reverse('userstory-statuses-detail', kwargs={"pk": data.blocked_user_story_status.pk})

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


def test_user_story_status_update(client, data):
    public_url = reverse('userstory-statuses-detail', kwargs={"pk": data.public_user_story_status.pk})
    private1_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status1.pk})
    private2_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status2.pk})
    blocked_url = reverse('userstory-statuses-detail', kwargs={"pk": data.blocked_user_story_status.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    user_story_status_data = serializers.UserStoryStatusSerializer(data.public_user_story_status).data
    user_story_status_data["name"] = "test"
    user_story_status_data = json.dumps(user_story_status_data)
    results = helper_test_http_method(client, 'put', public_url, user_story_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    user_story_status_data = serializers.UserStoryStatusSerializer(data.private_user_story_status1).data
    user_story_status_data["name"] = "test"
    user_story_status_data = json.dumps(user_story_status_data)
    results = helper_test_http_method(client, 'put', private1_url, user_story_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    user_story_status_data = serializers.UserStoryStatusSerializer(data.private_user_story_status2).data
    user_story_status_data["name"] = "test"
    user_story_status_data = json.dumps(user_story_status_data)
    results = helper_test_http_method(client, 'put', private2_url, user_story_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    user_story_status_data = serializers.UserStoryStatusSerializer(data.blocked_user_story_status).data
    user_story_status_data["name"] = "test"
    user_story_status_data = json.dumps(user_story_status_data)
    results = helper_test_http_method(client, 'put', blocked_url, user_story_status_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_user_story_status_delete(client, data):
    public_url = reverse('userstory-statuses-detail', kwargs={"pk": data.public_user_story_status.pk})
    private1_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status1.pk})
    private2_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status2.pk})
    blocked_url = reverse('userstory-statuses-detail', kwargs={"pk": data.blocked_user_story_status.pk})

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



def test_user_story_status_list(client, data):
    url = reverse('userstory-statuses-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_user_story_status_patch(client, data):
    public_url = reverse('userstory-statuses-detail', kwargs={"pk": data.public_user_story_status.pk})
    private1_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status1.pk})
    private2_url = reverse('userstory-statuses-detail', kwargs={"pk": data.private_user_story_status2.pk})
    blocked_url = reverse('userstory-statuses-detail', kwargs={"pk": data.blocked_user_story_status.pk})

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


def test_user_story_status_action_bulk_update_order(client, data):
    url = reverse('userstory-statuses-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_userstory_statuses": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_userstory_statuses": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_userstory_statuses": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_userstory_statuses": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_task_status_retrieve(client, data):
    public_url = reverse('task-statuses-detail', kwargs={"pk": data.public_task_status.pk})
    private1_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status1.pk})
    private2_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status2.pk})
    blocked_url = reverse('task-statuses-detail', kwargs={"pk": data.blocked_task_status.pk})

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


def test_task_status_update(client, data):
    public_url = reverse('task-statuses-detail', kwargs={"pk": data.public_task_status.pk})
    private1_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status1.pk})
    private2_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status2.pk})
    blocked_url = reverse('task-statuses-detail', kwargs={"pk": data.blocked_task_status.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    task_status_data = serializers.TaskStatusSerializer(data.public_task_status).data
    task_status_data["name"] = "test"
    task_status_data = json.dumps(task_status_data)
    results = helper_test_http_method(client, 'put', public_url, task_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_status_data = serializers.TaskStatusSerializer(data.private_task_status1).data
    task_status_data["name"] = "test"
    task_status_data = json.dumps(task_status_data)
    results = helper_test_http_method(client, 'put', private1_url, task_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_status_data = serializers.TaskStatusSerializer(data.private_task_status2).data
    task_status_data["name"] = "test"
    task_status_data = json.dumps(task_status_data)
    results = helper_test_http_method(client, 'put', private2_url, task_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    task_status_data = serializers.TaskStatusSerializer(data.blocked_task_status).data
    task_status_data["name"] = "test"
    task_status_data = json.dumps(task_status_data)
    results = helper_test_http_method(client, 'put', blocked_url, task_status_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_task_status_delete(client, data):
    public_url = reverse('task-statuses-detail', kwargs={"pk": data.public_task_status.pk})
    private1_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status1.pk})
    private2_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status2.pk})
    blocked_url = reverse('task-statuses-detail', kwargs={"pk": data.blocked_task_status.pk})

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



def test_task_status_list(client, data):
    url = reverse('task-statuses-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_task_status_patch(client, data):
    public_url = reverse('task-statuses-detail', kwargs={"pk": data.public_task_status.pk})
    private1_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status1.pk})
    private2_url = reverse('task-statuses-detail', kwargs={"pk": data.private_task_status2.pk})
    blocked_url = reverse('task-statuses-detail', kwargs={"pk": data.blocked_task_status.pk})

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


def test_task_status_action_bulk_update_order(client, data):
    url = reverse('task-statuses-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_task_statuses": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_statuses": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_statuses": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_task_statuses": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_issue_status_retrieve(client, data):
    public_url = reverse('issue-statuses-detail', kwargs={"pk": data.public_issue_status.pk})
    private1_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status1.pk})
    private2_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status2.pk})
    blocked_url = reverse('issue-statuses-detail', kwargs={"pk": data.blocked_issue_status.pk})

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


def test_issue_status_update(client, data):
    public_url = reverse('issue-statuses-detail', kwargs={"pk": data.public_issue_status.pk})
    private1_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status1.pk})
    private2_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status2.pk})
    blocked_url = reverse('issue-statuses-detail', kwargs={"pk": data.blocked_issue_status.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    issue_status_data = serializers.IssueStatusSerializer(data.public_issue_status).data
    issue_status_data["name"] = "test"
    issue_status_data = json.dumps(issue_status_data)
    results = helper_test_http_method(client, 'put', public_url, issue_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_status_data = serializers.IssueStatusSerializer(data.private_issue_status1).data
    issue_status_data["name"] = "test"
    issue_status_data = json.dumps(issue_status_data)
    results = helper_test_http_method(client, 'put', private1_url, issue_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_status_data = serializers.IssueStatusSerializer(data.private_issue_status2).data
    issue_status_data["name"] = "test"
    issue_status_data = json.dumps(issue_status_data)
    results = helper_test_http_method(client, 'put', private2_url, issue_status_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_status_data = serializers.IssueStatusSerializer(data.blocked_issue_status).data
    issue_status_data["name"] = "test"
    issue_status_data = json.dumps(issue_status_data)
    results = helper_test_http_method(client, 'put', blocked_url, issue_status_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_issue_status_delete(client, data):
    public_url = reverse('issue-statuses-detail', kwargs={"pk": data.public_issue_status.pk})
    private1_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status1.pk})
    private2_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status2.pk})
    blocked_url = reverse('issue-statuses-detail', kwargs={"pk": data.blocked_issue_status.pk})

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


def test_issue_status_list(client, data):
    url = reverse('issue-statuses-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_issue_status_patch(client, data):
    public_url = reverse('issue-statuses-detail', kwargs={"pk": data.public_issue_status.pk})
    private1_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status1.pk})
    private2_url = reverse('issue-statuses-detail', kwargs={"pk": data.private_issue_status2.pk})
    blocked_url = reverse('issue-statuses-detail', kwargs={"pk": data.blocked_issue_status.pk})

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


def test_issue_status_action_bulk_update_order(client, data):
    url = reverse('issue-statuses-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_issue_statuses": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_statuses": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_statuses": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_statuses": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_issue_type_retrieve(client, data):
    public_url = reverse('issue-types-detail', kwargs={"pk": data.public_issue_type.pk})
    private1_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type1.pk})
    private2_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type2.pk})
    blocked_url = reverse('issue-types-detail', kwargs={"pk": data.blocked_issue_type.pk})

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


def test_issue_type_update(client, data):
    public_url = reverse('issue-types-detail', kwargs={"pk": data.public_issue_type.pk})
    private1_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type1.pk})
    private2_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type2.pk})
    blocked_url = reverse('issue-types-detail', kwargs={"pk": data.blocked_issue_type.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    issue_type_data = serializers.IssueTypeSerializer(data.public_issue_type).data
    issue_type_data["name"] = "test"
    issue_type_data = json.dumps(issue_type_data)
    results = helper_test_http_method(client, 'put', public_url, issue_type_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_type_data = serializers.IssueTypeSerializer(data.private_issue_type1).data
    issue_type_data["name"] = "test"
    issue_type_data = json.dumps(issue_type_data)
    results = helper_test_http_method(client, 'put', private1_url, issue_type_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_type_data = serializers.IssueTypeSerializer(data.private_issue_type2).data
    issue_type_data["name"] = "test"
    issue_type_data = json.dumps(issue_type_data)
    results = helper_test_http_method(client, 'put', private2_url, issue_type_data, users)
    assert results == [401, 403, 403, 403, 200]

    issue_type_data = serializers.IssueTypeSerializer(data.blocked_issue_type).data
    issue_type_data["name"] = "test"
    issue_type_data = json.dumps(issue_type_data)
    results = helper_test_http_method(client, 'put', blocked_url, issue_type_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_issue_type_delete(client, data):
    public_url = reverse('issue-types-detail', kwargs={"pk": data.public_issue_type.pk})
    private1_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type1.pk})
    private2_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type2.pk})
    blocked_url = reverse('issue-types-detail', kwargs={"pk": data.blocked_issue_type.pk})

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


def test_issue_type_list(client, data):
    url = reverse('issue-types-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_issue_type_patch(client, data):
    public_url = reverse('issue-types-detail', kwargs={"pk": data.public_issue_type.pk})
    private1_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type1.pk})
    private2_url = reverse('issue-types-detail', kwargs={"pk": data.private_issue_type2.pk})
    blocked_url = reverse('issue-types-detail', kwargs={"pk": data.blocked_issue_type.pk})

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


def test_issue_type_action_bulk_update_order(client, data):
    url = reverse('issue-types-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_issue_types": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_types": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_types": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_issue_types": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_priority_retrieve(client, data):
    public_url = reverse('priorities-detail', kwargs={"pk": data.public_priority.pk})
    private1_url = reverse('priorities-detail', kwargs={"pk": data.private_priority1.pk})
    private2_url = reverse('priorities-detail', kwargs={"pk": data.private_priority2.pk})
    blocked_url = reverse('priorities-detail', kwargs={"pk": data.blocked_priority.pk})

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


def test_priority_update(client, data):
    public_url = reverse('priorities-detail', kwargs={"pk": data.public_priority.pk})
    private1_url = reverse('priorities-detail', kwargs={"pk": data.private_priority1.pk})
    private2_url = reverse('priorities-detail', kwargs={"pk": data.private_priority2.pk})
    blocked_url = reverse('priorities-detail', kwargs={"pk": data.blocked_priority.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    priority_data = serializers.PrioritySerializer(data.public_priority).data
    priority_data["name"] = "test"
    priority_data = json.dumps(priority_data)
    results = helper_test_http_method(client, 'put', public_url, priority_data, users)
    assert results == [401, 403, 403, 403, 200]

    priority_data = serializers.PrioritySerializer(data.private_priority1).data
    priority_data["name"] = "test"
    priority_data = json.dumps(priority_data)
    results = helper_test_http_method(client, 'put', private1_url, priority_data, users)
    assert results == [401, 403, 403, 403, 200]

    priority_data = serializers.PrioritySerializer(data.private_priority2).data
    priority_data["name"] = "test"
    priority_data = json.dumps(priority_data)
    results = helper_test_http_method(client, 'put', private2_url, priority_data, users)
    assert results == [401, 403, 403, 403, 200]

    priority_data = serializers.PrioritySerializer(data.blocked_priority).data
    priority_data["name"] = "test"
    priority_data = json.dumps(priority_data)
    results = helper_test_http_method(client, 'put', blocked_url, priority_data, users)
    assert results == [401, 403, 403, 403, 451]

def test_priority_delete(client, data):
    public_url = reverse('priorities-detail', kwargs={"pk": data.public_priority.pk})
    private1_url = reverse('priorities-detail', kwargs={"pk": data.private_priority1.pk})
    private2_url = reverse('priorities-detail', kwargs={"pk": data.private_priority2.pk})
    blocked_url = reverse('priorities-detail', kwargs={"pk": data.blocked_priority.pk})

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


def test_priority_list(client, data):
    url = reverse('priorities-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_priority_patch(client, data):
    public_url = reverse('priorities-detail', kwargs={"pk": data.public_priority.pk})
    private1_url = reverse('priorities-detail', kwargs={"pk": data.private_priority1.pk})
    private2_url = reverse('priorities-detail', kwargs={"pk": data.private_priority2.pk})
    blocked_url = reverse('priorities-detail', kwargs={"pk": data.blocked_priority.pk})

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


def test_priority_action_bulk_update_order(client, data):
    url = reverse('priorities-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_priorities": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_priorities": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_priorities": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_priorities": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_severity_retrieve(client, data):
    public_url = reverse('severities-detail', kwargs={"pk": data.public_severity.pk})
    private1_url = reverse('severities-detail', kwargs={"pk": data.private_severity1.pk})
    private2_url = reverse('severities-detail', kwargs={"pk": data.private_severity2.pk})
    blocked_url = reverse('severities-detail', kwargs={"pk": data.blocked_severity.pk})

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


def test_severity_update(client, data):
    public_url = reverse('severities-detail', kwargs={"pk": data.public_severity.pk})
    private1_url = reverse('severities-detail', kwargs={"pk": data.private_severity1.pk})
    private2_url = reverse('severities-detail', kwargs={"pk": data.private_severity2.pk})
    blocked_url = reverse('severities-detail', kwargs={"pk": data.blocked_severity.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    severity_data = serializers.SeveritySerializer(data.public_severity).data
    severity_data["name"] = "test"
    severity_data = json.dumps(severity_data)
    results = helper_test_http_method(client, 'put', public_url, severity_data, users)
    assert results == [401, 403, 403, 403, 200]

    severity_data = serializers.SeveritySerializer(data.private_severity1).data
    severity_data["name"] = "test"
    severity_data = json.dumps(severity_data)
    results = helper_test_http_method(client, 'put', private1_url, severity_data, users)
    assert results == [401, 403, 403, 403, 200]

    severity_data = serializers.SeveritySerializer(data.private_severity2).data
    severity_data["name"] = "test"
    severity_data = json.dumps(severity_data)
    results = helper_test_http_method(client, 'put', private2_url, severity_data, users)
    assert results == [401, 403, 403, 403, 200]

    severity_data = serializers.SeveritySerializer(data.blocked_severity).data
    severity_data["name"] = "test"
    severity_data = json.dumps(severity_data)
    results = helper_test_http_method(client, 'put', blocked_url, severity_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_severity_delete(client, data):
    public_url = reverse('severities-detail', kwargs={"pk": data.public_severity.pk})
    private1_url = reverse('severities-detail', kwargs={"pk": data.private_severity1.pk})
    private2_url = reverse('severities-detail', kwargs={"pk": data.private_severity2.pk})
    blocked_url = reverse('severities-detail', kwargs={"pk": data.blocked_severity.pk})

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


def test_severity_list(client, data):
    url = reverse('severities-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 4
    assert response.status_code == 200


def test_severity_patch(client, data):
    public_url = reverse('severities-detail', kwargs={"pk": data.public_severity.pk})
    private1_url = reverse('severities-detail', kwargs={"pk": data.private_severity1.pk})
    private2_url = reverse('severities-detail', kwargs={"pk": data.private_severity2.pk})
    blocked_url = reverse('severities-detail', kwargs={"pk": data.blocked_severity.pk})

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


def test_severity_action_bulk_update_order(client, data):
    url = reverse('severities-bulk-update-order')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    post_data = json.dumps({
        "bulk_severities": [(1, 2)],
        "project": data.public_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_severities": [(1, 2)],
        "project": data.private_project1.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_severities": [(1, 2)],
        "project": data.private_project2.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 204]

    post_data = json.dumps({
        "bulk_severities": [(1, 2)],
        "project": data.blocked_project.pk
    })
    results = helper_test_http_method(client, 'post', url, post_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_membership_retrieve(client, data):
    public_url = reverse('memberships-detail', kwargs={"pk": data.public_membership.pk})
    private1_url = reverse('memberships-detail', kwargs={"pk": data.private_membership1.pk})
    private2_url = reverse('memberships-detail', kwargs={"pk": data.private_membership2.pk})
    blocked_url = reverse('memberships-detail', kwargs={"pk": data.blocked_membership.pk})

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


def test_membership_update(client, data):
    public_url = reverse('memberships-detail', kwargs={"pk": data.public_membership.pk})
    private1_url = reverse('memberships-detail', kwargs={"pk": data.private_membership1.pk})
    private2_url = reverse('memberships-detail', kwargs={"pk": data.private_membership2.pk})
    blocked_url = reverse('memberships-detail', kwargs={"pk": data.blocked_membership.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    membership_data = serializers.MembershipSerializer(data.public_membership).data
    membership_data["token"] = "test"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'put', public_url, membership_data, users)
    assert results == [401, 403, 403, 403, 200]

    membership_data = serializers.MembershipSerializer(data.private_membership1).data
    membership_data["token"] = "test"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'put', private1_url, membership_data, users)
    assert results == [401, 403, 403, 403, 200]

    membership_data = serializers.MembershipSerializer(data.private_membership2).data
    membership_data["token"] = "test"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'put', private2_url, membership_data, users)
    assert results == [401, 403, 403, 403, 200]

    membership_data = serializers.MembershipSerializer(data.blocked_membership).data
    membership_data["token"] = "test"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'put', blocked_url, membership_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_membership_delete(client, data):
    public_url = reverse('memberships-detail', kwargs={"pk": data.public_membership.pk})
    private1_url = reverse('memberships-detail', kwargs={"pk": data.private_membership1.pk})
    private2_url = reverse('memberships-detail', kwargs={"pk": data.private_membership2.pk})
    blocked_url = reverse('memberships-detail', kwargs={"pk": data.blocked_membership.pk})

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


def test_membership_list(client, data):
    url = reverse('memberships-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 5
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 5
    assert response.status_code == 200

    client.login(data.project_member_without_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 5
    assert response.status_code == 200

    client.login(data.project_member_with_perms)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 11
    assert response.status_code == 200

    client.login(data.project_owner)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 11
    assert response.status_code == 200


def test_membership_patch(client, data):
    public_url = reverse('memberships-detail', kwargs={"pk": data.public_membership.pk})
    private1_url = reverse('memberships-detail', kwargs={"pk": data.private_membership1.pk})
    private2_url = reverse('memberships-detail', kwargs={"pk": data.private_membership2.pk})
    blocked_url = reverse('memberships-detail', kwargs={"pk": data.blocked_membership.pk})

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


def test_membership_create(client, data):
    url = reverse('memberships-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    membership_data = serializers.MembershipSerializer(data.public_membership).data
    membership_data["id"] = None
    membership_data["email"] = "test1@test.com"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'post', url, membership_data, users)
    assert results == [401, 403, 403, 403, 201]

    membership_data = serializers.MembershipSerializer(data.private_membership1).data
    membership_data["id"] = None
    membership_data["email"] = "test2@test.com"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'post', url, membership_data, users)
    assert results == [401, 403, 403, 403, 201]

    membership_data = serializers.MembershipSerializer(data.private_membership2).data
    membership_data["id"] = None
    membership_data["email"] = "test3@test.com"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'post', url, membership_data, users)
    assert results == [401, 403, 403, 403, 201]

    membership_data = serializers.MembershipSerializer(data.blocked_membership).data
    membership_data["id"] = None
    membership_data["email"] = "test4@test.com"
    membership_data = json.dumps(membership_data)
    results = helper_test_http_method(client, 'post', url, membership_data, users)
    assert results == [401, 403, 403, 403, 451]


def test_membership_action_bulk_create(client, data):
    url = reverse('memberships-bulk-create')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = {
        "project_id": data.public_project.id,
        "bulk_memberships": [
            {"role_id": data.public_membership.role.pk, "email": "test1@test.com"},
            {"role_id": data.public_membership.role.pk, "email": "test2@test.com"},
        ]
    }
    bulk_data = json.dumps(bulk_data)
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 403, 200]

    bulk_data = {
        "project_id": data.private_project1.id,
        "bulk_memberships": [
            {"role_id": data.private_membership1.role.pk, "email": "test1@test.com"},
            {"role_id": data.private_membership1.role.pk, "email": "test2@test.com"},
        ]
    }
    bulk_data = json.dumps(bulk_data)
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 403, 200]

    bulk_data = {
        "project_id": data.private_project2.id,
        "bulk_memberships": [
            {"role_id": data.private_membership2.role.pk, "email": "test1@test.com"},
            {"role_id": data.private_membership2.role.pk, "email": "test2@test.com"},
        ]
    }
    bulk_data = json.dumps(bulk_data)
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 403, 200]

    bulk_data = {
        "project_id": data.blocked_project.id,
        "bulk_memberships": [
            {"role_id": data.private_membership2.role.pk, "email": "test1@test.com"},
            {"role_id": data.private_membership2.role.pk, "email": "test2@test.com"},
        ]
    }
    bulk_data = json.dumps(bulk_data)
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 403, 451]

def test_membership_action_resend_invitation(client, data):
    public_invitation = f.InvitationFactory(project=data.public_project, role__project=data.public_project)
    private_invitation1 = f.InvitationFactory(project=data.private_project1, role__project=data.private_project1)
    private_invitation2 = f.InvitationFactory(project=data.private_project2, role__project=data.private_project2)
    blocked_invitation = f.InvitationFactory(project=data.blocked_project, role__project=data.blocked_project)

    public_url = reverse('memberships-resend-invitation', kwargs={"pk": public_invitation.pk})
    private1_url = reverse('memberships-resend-invitation', kwargs={"pk": private_invitation1.pk})
    private2_url = reverse('memberships-resend-invitation', kwargs={"pk": private_invitation2.pk})
    blocked_url = reverse('memberships-resend-invitation', kwargs={"pk": blocked_invitation.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 403, 403, 403, 204]

    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 403, 403, 403, 204]

    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 404, 403, 204]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 404, 403, 451]


def test_project_template_retrieve(client, data):
    url = reverse('project-templates-detail', kwargs={"pk": data.project_template.pk})

    users = [
        None,
        data.registered_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200]


def test_project_template_update(client, data):
    url = reverse('project-templates-detail', kwargs={"pk": data.project_template.pk})

    users = [
        None,
        data.registered_user,
        data.superuser,
    ]

    project_template_data = serializers.ProjectTemplateSerializer(data.project_template).data
    project_template_data["default_owner_role"] = "test"
    project_template_data = json.dumps(project_template_data)
    results = helper_test_http_method(client, 'put', url, project_template_data, users)
    assert results == [401, 403, 200]


def test_project_template_delete(client, data):
    url = reverse('project-templates-detail', kwargs={"pk": data.project_template.pk})

    users = [
        None,
        data.registered_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'delete', url, None, users)
    assert results == [401, 403, 204]


def test_project_template_list(client, data):
    url = reverse('project-templates-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 1
    assert response.status_code == 200

    client.login(data.registered_user)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 1
    assert response.status_code == 200

    client.login(data.superuser)
    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 1
    assert response.status_code == 200


def test_project_template_patch(client, data):
    url = reverse('project-templates-detail', kwargs={"pk": data.project_template.pk})

    users = [
        None,
        data.registered_user,
        data.superuser,
    ]

    results = helper_test_http_method(client, 'patch', url, '{"name": "Test"}', users)
    assert results == [401, 403, 200]
