# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

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

    m.registered_user = f.UserFactory.create()
    m.project_member_with_perms = f.UserFactory.create()
    m.project_member_without_perms = f.UserFactory.create()
    m.project_owner = f.UserFactory.create()
    m.other_user = f.UserFactory.create()

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


@pytest.fixture
def data_us(data):
    m = type("Models", (object,), {})
    m.public_user_story = f.UserStoryFactory(project=data.public_project, ref=1)
    m.private_user_story1 = f.UserStoryFactory(project=data.private_project1, ref=5)
    m.private_user_story2 = f.UserStoryFactory(project=data.private_project2, ref=9)
    return m


@pytest.fixture
def data_task(data):
    m = type("Models", (object,), {})
    m.public_task = f.TaskFactory(project=data.public_project, ref=2)
    m.private_task1 = f.TaskFactory(project=data.private_project1, ref=6)
    m.private_task2 = f.TaskFactory(project=data.private_project2, ref=10)
    return m


@pytest.fixture
def data_issue(data):
    m = type("Models", (object,), {})
    m.public_issue = f.IssueFactory(project=data.public_project, ref=3)
    m.private_issue1 = f.IssueFactory(project=data.private_project1, ref=7)
    m.private_issue2 = f.IssueFactory(project=data.private_project2, ref=11)
    return m


@pytest.fixture
def data_wiki(data):
    m = type("Models", (object,), {})
    m.public_wiki = f.WikiPageFactory(project=data.public_project, slug=4)
    m.private_wiki1 = f.WikiPageFactory(project=data.private_project1, slug=8)
    m.private_wiki2 = f.WikiPageFactory(project=data.private_project2, slug=12)
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
