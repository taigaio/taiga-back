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
from django.utils import timezone

from taiga.base.utils import json
from taiga.permissions.choices import MEMBERS_PERMISSIONS, ANON_PERMISSIONS
from taiga.projects.history.models import HistoryEntry
from taiga.projects.history.choices import HistoryType
from taiga.projects.history.services import make_key_from_model_object

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals

import pytest
pytestmark = pytest.mark.django_db


def setup_module(module):
    disconnect_signals()


def teardown_module(module):
    reconnect_signals()


@pytest.fixture
def data():
    m = type("Models", (object,), {})

    m.registered_user = f.UserFactory.create(full_name="registered_user")
    m.project_member_with_perms = f.UserFactory.create(full_name="project_member_with_perms")
    m.project_member_without_perms = f.UserFactory.create(full_name="project_member_without_perms")
    m.project_owner = f.UserFactory.create(full_name="project_owner")
    m.other_user = f.UserFactory.create(full_name="other_user")

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
                        is_admin=True)

    f.MembershipFactory(project=m.private_project1,
                        user=m.project_owner,
                        is_admin=True)

    f.MembershipFactory(project=m.private_project2,
                        user=m.project_owner,
                        is_admin=True)
    return m


#########################################################
## User stories
#########################################################


@pytest.fixture
def data_us(data):
    m = type("Models", (object,), {})
    m.public_user_story = f.UserStoryFactory(project=data.public_project, ref=1)
    m.public_history_entry = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.public_project,
                                                          comment="testing public",
                                                          key=make_key_from_model_object(m.public_user_story),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})

    m.private_user_story1 = f.UserStoryFactory(project=data.private_project1, ref=5)
    m.private_history_entry1 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project1,
                                                          comment="testing 1",
                                                          key=make_key_from_model_object(m.private_user_story1),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    m.private_user_story2 = f.UserStoryFactory(project=data.private_project2, ref=9)
    m.private_history_entry2 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project2,
                                                          comment="testing 2",
                                                          key=make_key_from_model_object(m.private_user_story2),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    return m


def test_user_story_history_retrieve(client, data, data_us):
    public_url = reverse('userstory-history-detail', kwargs={"pk": data_us.public_user_story.pk})
    private_url1 = reverse('userstory-history-detail', kwargs={"pk": data_us.private_user_story1.pk})
    private_url2 = reverse('userstory-history-detail', kwargs={"pk": data_us.private_user_story2.pk})

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


def test_user_story_action_edit_comment(client, data, data_us):
    public_url = "{}?id={}".format(
        reverse('userstory-history-edit-comment', kwargs={"pk": data_us.public_user_story.pk}),
        data_us.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('userstory-history-edit-comment', kwargs={"pk": data_us.private_user_story1.pk}),
        data_us.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('userstory-history-edit-comment', kwargs={"pk": data_us.private_user_story2.pk}),
        data_us.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    data = json.dumps({"comment": "testing update comment"})

    results = helper_test_http_method(client, 'post', public_url, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, data, users)
    assert results == [401, 403, 403, 200, 200]


def test_user_story_action_delete_comment(client, data, data_us):
    public_url = "{}?id={}".format(
        reverse('userstory-history-delete-comment', kwargs={"pk": data_us.public_user_story.pk}),
        data_us.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('userstory-history-delete-comment', kwargs={"pk": data_us.private_user_story1.pk}),
        data_us.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('userstory-history-delete-comment', kwargs={"pk": data_us.private_user_story2.pk}),
        data_us.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_us.public_history_entry.delete_comment_date = None
        data_us.public_history_entry.delete_comment_user = None
        data_us.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_us.private_history_entry1.delete_comment_date = None
        data_us.private_history_entry1.delete_comment_user = None
        data_us.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_us.private_history_entry2.delete_comment_date = None
        data_us.private_history_entry2.delete_comment_user = None
        data_us.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_user_story_action_undelete_comment(client, data, data_us):
    public_url = "{}?id={}".format(
        reverse('userstory-history-undelete-comment', kwargs={"pk": data_us.public_user_story.pk}),
        data_us.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('userstory-history-undelete-comment', kwargs={"pk": data_us.private_user_story1.pk}),
        data_us.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('userstory-history-undelete-comment', kwargs={"pk": data_us.private_user_story2.pk}),
        data_us.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_us.public_history_entry.delete_comment_date = timezone.now()
        data_us.public_history_entry.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_us.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_us.private_history_entry1.delete_comment_date = timezone.now()
        data_us.private_history_entry1.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_us.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_us.private_history_entry2.delete_comment_date = timezone.now()
        data_us.private_history_entry2.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_us.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_user_story_action_comment_versions(client, data, data_us):
    public_url = "{}?id={}".format(
        reverse('userstory-history-comment-versions', kwargs={"pk": data_us.public_user_story.pk}),
        data_us.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('userstory-history-comment-versions', kwargs={"pk": data_us.private_user_story1.pk}),
        data_us.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('userstory-history-comment-versions', kwargs={"pk": data_us.private_user_story2.pk}),
        data_us.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner,
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


#########################################################
## Tasks
#########################################################


@pytest.fixture
def data_task(data):
    m = type("Models", (object,), {})
    m.public_task = f.TaskFactory(project=data.public_project, ref=2)
    m.public_history_entry = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.public_project,
                                                          comment="testing public",
                                                          key=make_key_from_model_object(m.public_task),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})

    m.private_task1 = f.TaskFactory(project=data.private_project1, ref=6)
    m.private_history_entry1 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project1,
                                                          comment="testing 1",
                                                          key=make_key_from_model_object(m.private_task1),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    m.private_task2 = f.TaskFactory(project=data.private_project2, ref=10)
    m.private_history_entry2 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project2,
                                                          comment="testing 2",
                                                          key=make_key_from_model_object(m.private_task2),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    return m


def test_task_history_retrieve(client, data, data_task):
    public_url = reverse('task-history-detail', kwargs={"pk": data_task.public_task.pk})
    private_url1 = reverse('task-history-detail', kwargs={"pk": data_task.private_task1.pk})
    private_url2 = reverse('task-history-detail', kwargs={"pk": data_task.private_task2.pk})

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


def test_task_action_edit_comment(client, data, data_task):
    public_url = "{}?id={}".format(
        reverse('task-history-edit-comment', kwargs={"pk": data_task.public_task.pk}),
        data_task.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('task-history-edit-comment', kwargs={"pk": data_task.private_task1.pk}),
        data_task.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('task-history-edit-comment', kwargs={"pk": data_task.private_task2.pk}),
        data_task.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    data = json.dumps({"comment": "testing update comment"})

    results = helper_test_http_method(client, 'post', public_url, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, data, users)
    assert results == [401, 403, 403, 200, 200]


def test_task_action_delete_comment(client, data, data_task):
    public_url = "{}?id={}".format(
        reverse('task-history-delete-comment', kwargs={"pk": data_task.public_task.pk}),
        data_task.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('task-history-delete-comment', kwargs={"pk": data_task.private_task1.pk}),
        data_task.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('task-history-delete-comment', kwargs={"pk": data_task.private_task2.pk}),
        data_task.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_task.public_history_entry.delete_comment_date = None
        data_task.public_history_entry.delete_comment_user = None
        data_task.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_task.private_history_entry1.delete_comment_date = None
        data_task.private_history_entry1.delete_comment_user = None
        data_task.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_task.private_history_entry2.delete_comment_date = None
        data_task.private_history_entry2.delete_comment_user = None
        data_task.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_task_action_undelete_comment(client, data, data_task):
    public_url = "{}?id={}".format(
        reverse('task-history-undelete-comment', kwargs={"pk": data_task.public_task.pk}),
        data_task.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('task-history-undelete-comment', kwargs={"pk": data_task.private_task1.pk}),
        data_task.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('task-history-undelete-comment', kwargs={"pk": data_task.private_task2.pk}),
        data_task.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_task.public_history_entry.delete_comment_date = timezone.now()
        data_task.public_history_entry.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_task.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_task.private_history_entry1.delete_comment_date = timezone.now()
        data_task.private_history_entry1.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_task.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_task.private_history_entry2.delete_comment_date = timezone.now()
        data_task.private_history_entry2.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_task.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_task_action_comment_versions(client, data, data_task):
    public_url = "{}?id={}".format(
        reverse('task-history-comment-versions', kwargs={"pk": data_task.public_task.pk}),
        data_task.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('task-history-comment-versions', kwargs={"pk": data_task.private_task1.pk}),
        data_task.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('task-history-comment-versions', kwargs={"pk": data_task.private_task2.pk}),
        data_task.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner,
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


#########################################################
## Issues
#########################################################


@pytest.fixture
def data_issue(data):
    m = type("Models", (object,), {})
    m.public_issue = f.IssueFactory(project=data.public_project, ref=3)
    m.public_history_entry = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.public_project,
                                                          comment="testing public",
                                                          key=make_key_from_model_object(m.public_issue),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})

    m.private_issue1 = f.IssueFactory(project=data.private_project1, ref=7)
    m.private_history_entry1 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project1,
                                                          comment="testing 1",
                                                          key=make_key_from_model_object(m.private_issue1),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    m.private_issue2 = f.IssueFactory(project=data.private_project2, ref=11)
    m.private_history_entry2 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project2,
                                                          comment="testing 2",
                                                          key=make_key_from_model_object(m.private_issue2),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    return m


def test_issue_history_retrieve(client, data, data_issue):
    public_url = reverse('issue-history-detail', kwargs={"pk": data_issue.public_issue.pk})
    private_url1 = reverse('issue-history-detail', kwargs={"pk": data_issue.private_issue1.pk})
    private_url2 = reverse('issue-history-detail', kwargs={"pk": data_issue.private_issue2.pk})

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


def test_issue_action_edit_comment(client, data, data_issue):
    public_url = "{}?id={}".format(
        reverse('issue-history-edit-comment', kwargs={"pk": data_issue.public_issue.pk}),
        data_issue.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('issue-history-edit-comment', kwargs={"pk": data_issue.private_issue1.pk}),
        data_issue.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('issue-history-edit-comment', kwargs={"pk": data_issue.private_issue2.pk}),
        data_issue.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    data = json.dumps({"comment": "testing update comment"})

    results = helper_test_http_method(client, 'post', public_url, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, data, users)
    assert results == [401, 403, 403, 200, 200]


def test_issue_action_delete_comment(client, data, data_issue):
    public_url = "{}?id={}".format(
        reverse('issue-history-delete-comment', kwargs={"pk": data_issue.public_issue.pk}),
        data_issue.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('issue-history-delete-comment', kwargs={"pk": data_issue.private_issue1.pk}),
        data_issue.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('issue-history-delete-comment', kwargs={"pk": data_issue.private_issue2.pk}),
        data_issue.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_issue.public_history_entry.delete_comment_date = None
        data_issue.public_history_entry.delete_comment_user = None
        data_issue.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_issue.private_history_entry1.delete_comment_date = None
        data_issue.private_history_entry1.delete_comment_user = None
        data_issue.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_issue.private_history_entry2.delete_comment_date = None
        data_issue.private_history_entry2.delete_comment_user = None
        data_issue.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_issue_action_undelete_comment(client, data, data_issue):
    public_url = "{}?id={}".format(
        reverse('issue-history-undelete-comment', kwargs={"pk": data_issue.public_issue.pk}),
        data_issue.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('issue-history-undelete-comment', kwargs={"pk": data_issue.private_issue1.pk}),
        data_issue.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('issue-history-undelete-comment', kwargs={"pk": data_issue.private_issue2.pk}),
        data_issue.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_issue.public_history_entry.delete_comment_date = timezone.now()
        data_issue.public_history_entry.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_issue.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_issue.private_history_entry1.delete_comment_date = timezone.now()
        data_issue.private_history_entry1.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_issue.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_issue.private_history_entry2.delete_comment_date = timezone.now()
        data_issue.private_history_entry2.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_issue.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_issue_action_comment_versions(client, data, data_issue):
    public_url = "{}?id={}".format(
        reverse('issue-history-comment-versions', kwargs={"pk": data_issue.public_issue.pk}),
        data_issue.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('issue-history-comment-versions', kwargs={"pk": data_issue.private_issue1.pk}),
        data_issue.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('issue-history-comment-versions', kwargs={"pk": data_issue.private_issue2.pk}),
        data_issue.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner,
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]


#########################################################
## Wiki pages
#########################################################


@pytest.fixture
def data_wiki(data):
    m = type("Models", (object,), {})
    m.public_wiki = f.WikiPageFactory(project=data.public_project, slug=4)
    m.public_history_entry = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.public_project,
                                                          comment="testing public",
                                                          key=make_key_from_model_object(m.public_wiki),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})

    m.private_wiki1 = f.WikiPageFactory(project=data.private_project1, slug=8)
    m.private_history_entry1 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project1,
                                                          comment="testing 1",
                                                          key=make_key_from_model_object(m.private_wiki1),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    m.private_wiki2 = f.WikiPageFactory(project=data.private_project2, slug=12)
    m.private_history_entry2 = f.HistoryEntryFactory.create(type=HistoryType.change,
                                                          project=data.private_project2,
                                                          comment="testing 2",
                                                          key=make_key_from_model_object(m.private_wiki2),
                                                          diff={},
                                                          user={"pk": data.project_member_with_perms.pk})
    return m


def test_wiki_history_retrieve(client, data, data_wiki):
    public_url = reverse('wiki-history-detail', kwargs={"pk": data_wiki.public_wiki.pk})
    private_url1 = reverse('wiki-history-detail', kwargs={"pk": data_wiki.private_wiki1.pk})
    private_url2 = reverse('wiki-history-detail', kwargs={"pk": data_wiki.private_wiki2.pk})

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


def test_wiki_action_edit_comment(client, data, data_wiki):
    public_url = "{}?id={}".format(
        reverse('wiki-history-edit-comment', kwargs={"pk": data_wiki.public_wiki.pk}),
        data_wiki.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('wiki-history-edit-comment', kwargs={"pk": data_wiki.private_wiki1.pk}),
        data_wiki.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('wiki-history-edit-comment', kwargs={"pk": data_wiki.private_wiki2.pk}),
        data_wiki.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    data = json.dumps({"comment": "testing update comment"})

    results = helper_test_http_method(client, 'post', public_url, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url1, data, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'post', private_url2, data, users)
    assert results == [401, 403, 403, 200, 200]


def test_wiki_action_delete_comment(client, data, data_wiki):
    public_url = "{}?id={}".format(
        reverse('wiki-history-delete-comment', kwargs={"pk": data_wiki.public_wiki.pk}),
        data_wiki.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('wiki-history-delete-comment', kwargs={"pk": data_wiki.private_wiki1.pk}),
        data_wiki.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('wiki-history-delete-comment', kwargs={"pk": data_wiki.private_wiki2.pk}),
        data_wiki.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_wiki.public_history_entry.delete_comment_date = None
        data_wiki.public_history_entry.delete_comment_user = None
        data_wiki.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_wiki.private_history_entry1.delete_comment_date = None
        data_wiki.private_history_entry1.delete_comment_user = None
        data_wiki.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_wiki.private_history_entry2.delete_comment_date = None
        data_wiki.private_history_entry2.delete_comment_user = None
        data_wiki.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_wiki_action_undelete_comment(client, data, data_wiki):
    public_url = "{}?id={}".format(
        reverse('wiki-history-undelete-comment', kwargs={"pk": data_wiki.public_wiki.pk}),
        data_wiki.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('wiki-history-undelete-comment', kwargs={"pk": data_wiki.private_wiki1.pk}),
        data_wiki.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('wiki-history-undelete-comment', kwargs={"pk": data_wiki.private_wiki2.pk}),
        data_wiki.private_history_entry2.id
    )

    users_and_statuses = [
        (None, 401),
        (data.registered_user, 403),
        (data.project_member_without_perms, 403),
        (data.project_member_with_perms, 200),
        (data.project_owner, 200),
    ]

    for user, status_code in users_and_statuses:
        data_wiki.public_history_entry.delete_comment_date = timezone.now()
        data_wiki.public_history_entry.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_wiki.public_history_entry.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(public_url)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_wiki.private_history_entry1.delete_comment_date = timezone.now()
        data_wiki.private_history_entry1.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_wiki.private_history_entry1.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url1)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage

    for user, status_code in users_and_statuses:
        data_wiki.private_history_entry2.delete_comment_date = timezone.now()
        data_wiki.private_history_entry2.delete_comment_user = {"pk": data.project_member_with_perms.pk}
        data_wiki.private_history_entry2.save()

        if user:
            client.login(user)
        else:
            client.logout()
        response = client.json.post(private_url2)
        error_mesage = "{} != {} for {}".format(response.status_code, status_code, user)
        assert response.status_code == status_code, error_mesage


def test_wiki_action_comment_versions(client, data, data_wiki):
    public_url = "{}?id={}".format(
        reverse('wiki-history-comment-versions', kwargs={"pk": data_wiki.public_wiki.pk}),
        data_wiki.public_history_entry.id
    )
    private_url1 = "{}?id={}".format(
        reverse('wiki-history-comment-versions', kwargs={"pk": data_wiki.private_wiki1.pk}),
        data_wiki.private_history_entry1.id
    )
    private_url2 = "{}?id={}".format(
        reverse('wiki-history-comment-versions', kwargs={"pk": data_wiki.private_wiki2.pk}),
        data_wiki.private_history_entry2.id
    )

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner,
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [401, 403, 403, 200, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [401, 403, 403, 200, 200]
