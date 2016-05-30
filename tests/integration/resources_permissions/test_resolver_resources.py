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
                                        owner=m.project_owner,
                                        slug="public")
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                          owner=m.project_owner,
                                          slug="private1")
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner,
                                          slug="private2")

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

    m.view_only_membership = f.MembershipFactory(project=m.private_project2,
                                                 user=m.other_user,
                                                 role__project=m.private_project2,
                                                 role__permissions=["view_project"])

    m.us = f.UserStoryFactory(project=m.private_project2, ref=1)
    m.task = f.TaskFactory(project=m.private_project2, ref=2)
    m.issue = f.IssueFactory(project=m.private_project2, ref=3)
    m.milestone = f.MilestoneFactory(project=m.private_project2, slug="milestone-test-1")

    return m


def test_resolver_list(client, data):
    url = reverse('resolver-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', "{}?project={}".format(url, data.public_project.slug), None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', "{}?project={}".format(url, data.private_project1.slug), None, users)
    assert results == [200, 200, 200, 200, 200]
    results = helper_test_http_method(client, 'get', "{}?project={}".format(url, data.private_project2.slug), None, users)
    assert results == [401, 403, 403, 200, 200]

    client.login(data.other_user)
    response = client.json.get("{}?project={}&us={}&task={}&issue={}&milestone={}".format(url,
                                                                                          data.private_project2.slug,
                                                                                          data.us.ref,
                                                                                          data.task.ref,
                                                                                          data.issue.ref,
                                                                                          data.milestone.slug))
    assert response.data == {"project": data.private_project2.pk}

    client.login(data.project_owner)
    response = client.json.get("{}?project={}&us={}&task={}&issue={}&milestone={}".format(url,
                                                                                          data.private_project2.slug,
                                                                                          data.us.ref,
                                                                                          data.task.ref,
                                                                                          data.issue.ref,
                                                                                          data.milestone.slug))
    assert response.data == {"project": data.private_project2.pk,
                             "us": data.us.pk,
                             "task": data.task.pk,
                             "issue": data.issue.pk,
                             "milestone": data.milestone.pk}

    response = client.json.get("{}?project={}&ref={}".format(url,
                                                             data.private_project2.slug,
                                                             data.us.ref))
    assert response.data == {"project": data.private_project2.pk,
                             "us": data.us.pk}

    response = client.json.get("{}?project={}&ref={}".format(url,
                                                             data.private_project2.slug,
                                                             data.task.ref))
    assert response.data == {"project": data.private_project2.pk,
                             "task": data.task.pk}

    response = client.json.get("{}?project={}&ref={}".format(url,
                                                             data.private_project2.slug,
                                                             data.issue.ref))
    assert response.data == {"project": data.private_project2.pk,
                             "issue": data.issue.pk}
