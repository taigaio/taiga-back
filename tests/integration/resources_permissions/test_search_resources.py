from django.core.urlresolvers import reverse

from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS

from tests import factories as f
from tests.utils import helper_test_http_method_and_keys, disconnect_signals, reconnect_signals

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

    m.public_issue = f.IssueFactory(project=m.public_project,
                                    status__project=m.public_project,
                                    severity__project=m.public_project,
                                    priority__project=m.public_project,
                                    type__project=m.public_project,
                                    milestone__project=m.public_project)
    m.private_issue1 = f.IssueFactory(project=m.private_project1,
                                      status__project=m.private_project1,
                                      severity__project=m.private_project1,
                                      priority__project=m.private_project1,
                                      type__project=m.private_project1,
                                      milestone__project=m.private_project1)
    m.private_issue2 = f.IssueFactory(project=m.private_project2,
                                      status__project=m.private_project2,
                                      severity__project=m.private_project2,
                                      priority__project=m.private_project2,
                                      type__project=m.private_project2,
                                      milestone__project=m.private_project2)

    return m


def test_search_list(client, data):
    url = reverse('search-list')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method_and_keys(client, 'get', url, {'project': data.public_project.pk}, users)
    all_keys = set(['count', 'userstories', 'issues', 'tasks', 'wikipages'])
    assert results == [(200, all_keys), (200, all_keys), (200, all_keys), (200, all_keys), (200, all_keys)]
    results = helper_test_http_method_and_keys(client, 'get', url, {'project': data.private_project1.pk}, users)
    assert results == [(200, all_keys), (200, all_keys), (200, all_keys), (200, all_keys), (200, all_keys)]
    results = helper_test_http_method_and_keys(client, 'get', url, {'project': data.private_project2.pk}, users)
    assert results == [(200, set(['count'])), (200, set(['count'])), (200, set(['count'])), (200, all_keys), (200, all_keys)]
