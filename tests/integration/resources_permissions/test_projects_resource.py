# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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
from django.apps import apps

from taiga.base.utils import json
from taiga.projects import choices as project_choices
from taiga.projects import models as project_models
from taiga.projects.serializers import ProjectSerializer
from taiga.permissions.choices import MEMBERS_PERMISSIONS
from taiga.projects.utils import attach_extra_info

from tests import factories as f
from tests.utils import helper_test_http_method, helper_test_http_method_and_count

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
                                        public_permissions=['view_project'])
    m.public_project = attach_extra_info(project_models.Project.objects.all()).get(id=m.public_project.id)

    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=['view_project'],
                                          public_permissions=['view_project'],
                                          owner=m.project_owner)
    m.private_project1 = attach_extra_info(project_models.Project.objects.all()).get(id=m.private_project1.id)

    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner)
    m.private_project2 = attach_extra_info(project_models.Project.objects.all()).get(id=m.private_project2.id)

    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF)
    m.blocked_project = attach_extra_info(project_models.Project.objects.all()).get(id=m.blocked_project.id)

    f.RoleFactory(project=m.public_project)

    m.membership = f.MembershipFactory(project=m.private_project1,
                                       user=m.project_member_with_perms,
                                       role__project=m.private_project1,
                                       role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.membership = f.MembershipFactory(project=m.private_project1,
                                       user=m.project_member_without_perms,
                                       role__project=m.private_project1,
                                       role__permissions=[])
    m.membership = f.MembershipFactory(project=m.private_project2,
                                       user=m.project_member_with_perms,
                                       role__project=m.private_project2,
                                       role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.membership = f.MembershipFactory(project=m.private_project2,
                                       user=m.project_member_without_perms,
                                       role__project=m.private_project2,
                                       role__permissions=[])
    m.membership = f.MembershipFactory(project=m.blocked_project,
                                       user=m.project_member_with_perms,
                                       role__project=m.blocked_project,
                                       role__permissions=list(map(lambda x: x[0], MEMBERS_PERMISSIONS)))
    m.membership = f.MembershipFactory(project=m.blocked_project,
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

    ContentType = apps.get_model("contenttypes", "ContentType")
    Project = apps.get_model("projects", "Project")

    project_ct = ContentType.objects.get_for_model(Project)

    f.LikeFactory(content_type=project_ct, object_id=m.public_project.pk, user=m.project_member_with_perms)
    f.LikeFactory(content_type=project_ct, object_id=m.public_project.pk, user=m.project_owner)
    f.LikeFactory(content_type=project_ct, object_id=m.private_project1.pk, user=m.project_member_with_perms)
    f.LikeFactory(content_type=project_ct, object_id=m.private_project1.pk, user=m.project_owner)
    f.LikeFactory(content_type=project_ct, object_id=m.private_project2.pk, user=m.project_member_with_perms)
    f.LikeFactory(content_type=project_ct, object_id=m.private_project2.pk, user=m.project_owner)
    f.LikeFactory(content_type=project_ct, object_id=m.blocked_project.pk, user=m.project_member_with_perms)
    f.LikeFactory(content_type=project_ct, object_id=m.blocked_project.pk, user=m.project_owner)

    return m


def test_project_retrieve(client, data):
    public_url = reverse('projects-detail', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-detail', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-detail', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-detail', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [401, 403, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 200, 200]


def test_project_update(client, data):
    url = reverse('projects-detail', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-detail', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]

    project_data = ProjectSerializer(data.private_project2).data
    project_data["is_private"] = False
    results = helper_test_http_method(client, 'put', url, json.dumps(project_data), users)
    assert results == [401, 403, 403, 200]

    project_data = ProjectSerializer(data.blocked_project).data
    project_data["is_private"] = False
    results = helper_test_http_method(client, 'put', blocked_url, json.dumps(project_data), users)
    assert results == [401, 403, 403, 451]


def test_project_delete(client, data):
    url = reverse('projects-detail', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-detail', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'delete', url, None, users)
    assert results == [401, 403, 403, 204]

    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [401, 403, 403, 451]


def test_project_list(client, data):
    url = reverse('projects-list')

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

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


def test_project_patch(client, data):
    url = reverse('projects-detail', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-detail', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    data = json.dumps({"is_private": False})

    results = helper_test_http_method(client, 'patch', url, data, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'patch', blocked_url, data, users)
    assert results == [401, 403, 403, 451]


def test_project_action_stats(client, data):
    public_url = reverse('projects-stats', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-stats', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-stats', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-stats', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [404, 404, 200, 200]


def test_project_action_issues_stats(client, data):
    public_url = reverse('projects-issues-stats', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-issues-stats', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-issues-stats', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-issues-stats', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [404, 404, 200, 200]


def test_project_action_like(client, data):
    public_url = reverse('projects-like', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-like', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-like', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-like', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 451, 451]


def test_project_action_unlike(client, data):
    public_url = reverse('projects-unlike', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-unlike', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-unlike', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-unlike', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 451, 451]


def test_project_fans_list(client, data):
    public_url = reverse('project-fans-list', kwargs={"resource_id": data.public_project.pk})
    private1_url = reverse('project-fans-list', kwargs={"resource_id": data.private_project1.pk})
    private2_url = reverse('project-fans-list', kwargs={"resource_id": data.private_project2.pk})
    blocked_url = reverse('project-fans-list', kwargs={"resource_id": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method_and_count(client, 'get', public_url, None, users)
    assert results == [(200, 2), (200, 2), (200, 2), (200, 2), (200, 2)]
    results = helper_test_http_method_and_count(client, 'get', private1_url, None, users)
    assert results == [(200, 2), (200, 2), (200, 2), (200, 2), (200, 2)]
    results = helper_test_http_method_and_count(client, 'get', private2_url, None, users)
    assert results == [(401, 0), (403, 0), (403, 0), (200, 2), (200, 2)]
    results = helper_test_http_method_and_count(client, 'get', blocked_url, None, users)
    assert results == [(401, 0), (403, 0), (403, 0), (200, 2), (200, 2)]


def test_project_fans_retrieve(client, data):
    public_url = reverse('project-fans-detail', kwargs={"resource_id": data.public_project.pk,
                                                      "pk": data.project_owner.pk})
    private1_url = reverse('project-fans-detail', kwargs={"resource_id": data.private_project1.pk,
                                                      "pk": data.project_owner.pk})
    private2_url = reverse('project-fans-detail', kwargs={"resource_id": data.private_project2.pk,
                                                      "pk": data.project_owner.pk})
    blocked_url = reverse('project-fans-detail', kwargs={"resource_id": data.blocked_project.pk,
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
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_project_watchers_list(client, data):
    public_url = reverse('project-watchers-list', kwargs={"resource_id": data.public_project.pk})
    private1_url = reverse('project-watchers-list', kwargs={"resource_id": data.private_project1.pk})
    private2_url = reverse('project-watchers-list', kwargs={"resource_id": data.private_project2.pk})
    blocked_url = reverse('project-watchers-list', kwargs={"resource_id": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method_and_count(client, 'get', public_url, None, users)
    assert results == [(200, 1), (200, 1), (200, 1), (200, 1), (200, 1)]
    results = helper_test_http_method_and_count(client, 'get', private1_url, None, users)
    assert results == [(200, 3), (200, 3), (200, 3), (200, 3), (200, 3)]
    results = helper_test_http_method_and_count(client, 'get', private2_url, None, users)
    assert results == [(401, 0), (403, 0), (403, 0), (200, 3), (200, 3)]
    results = helper_test_http_method_and_count(client, 'get', blocked_url, None, users)
    assert results == [(401, 0), (403, 0), (403, 0), (200, 3), (200, 3)]


def test_project_watchers_retrieve(client, data):
    public_url = reverse('project-watchers-detail', kwargs={"resource_id": data.public_project.pk,
                                                      "pk": data.project_owner.pk})
    private1_url = reverse('project-watchers-detail', kwargs={"resource_id": data.private_project1.pk,
                                                      "pk": data.project_owner.pk})
    private2_url = reverse('project-watchers-detail', kwargs={"resource_id": data.private_project2.pk,
                                                      "pk": data.project_owner.pk})
    blocked_url = reverse('project-watchers-detail', kwargs={"resource_id": data.blocked_project.pk,
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
    results = helper_test_http_method(client, 'get', private1_url, None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', private2_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [401, 403, 403, 200, 200]


def test_project_action_create_template(client, data):
    public_url = reverse('projects-create-template', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-create-template', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-create-template', kwargs={"pk": data.private_project2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner,
        data.superuser,
    ]

    template_data = json.dumps({
        "template_name": "test",
        "template_description": "test",
    })

    results = helper_test_http_method(client, 'post', public_url, template_data, users)
    assert results == [401, 403, 403, 403, 403, 201]
    results = helper_test_http_method(client, 'post', private1_url, template_data, users)
    assert results == [401, 403, 403, 403, 403, 201]
    results = helper_test_http_method(client, 'post', private2_url, template_data, users)
    assert results == [404, 404, 404, 403, 403, 201]


def test_invitations_list(client, data):
    url = reverse('invitations-list')

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [403, 403, 403, 403]


def test_invitations_retrieve(client, data):
    invitation = f.MembershipFactory(user=None)

    url = reverse('invitations-detail', kwargs={'token': invitation.token})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'get', url, None, users)
    assert results == [200, 200, 200, 200]


def test_regenerate_userstories_csv_uuid(client, data):
    public_url = reverse('projects-regenerate-userstories-csv-uuid', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-regenerate-userstories-csv-uuid', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-regenerate-userstories-csv-uuid', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-regenerate-userstories-csv-uuid', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 403, 200]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 403, 451]


def test_regenerate_tasks_csv_uuid(client, data):
    public_url = reverse('projects-regenerate-tasks-csv-uuid', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-regenerate-tasks-csv-uuid', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-regenerate-tasks-csv-uuid', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-regenerate-tasks-csv-uuid', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 403, 200]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 403, 451]


def test_regenerate_issues_csv_uuid(client, data):
    public_url = reverse('projects-regenerate-issues-csv-uuid', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-regenerate-issues-csv-uuid', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-regenerate-issues-csv-uuid', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-regenerate-issues-csv-uuid', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 403, 403, 200]

    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 403, 200]

    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 403, 451]


def test_project_action_watch(client, data):
    public_url = reverse('projects-watch', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-watch', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-watch', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-watch', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 451, 451]


def test_project_action_unwatch(client, data):
    public_url = reverse('projects-unwatch', kwargs={"pk": data.public_project.pk})
    private1_url = reverse('projects-unwatch', kwargs={"pk": data.private_project1.pk})
    private2_url = reverse('projects-unwatch', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-unwatch', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_with_perms,
        data.project_owner
    ]
    results = helper_test_http_method(client, 'post', public_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private1_url, None, users)
    assert results == [401, 200, 200, 200]
    results = helper_test_http_method(client, 'post', private2_url, None, users)
    assert results == [404, 404, 200, 200]
    results = helper_test_http_method(client, 'post', blocked_url, None, users)
    assert results == [404, 404, 451, 451]


def test_project_list_with_discover_mode_enabled(client, data):
    url = "{}?{}".format(reverse('projects-list'), "discover_mode=true")

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    projects_data = json.loads(response.content.decode('utf-8'))
    assert len(projects_data) == 2
    assert response.status_code == 200
