import uuid

from django.core.urlresolvers import reverse

from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS
from taiga.base.utils import json

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals
from taiga.projects import choices as project_choices
from taiga.projects.votes.services import add_vote
from taiga.projects.notifications.services import add_watcher
from taiga.projects.occ import OCCResourceMixin

from unittest import mock

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
    m.blocked_project = f.ProjectFactory(is_private=True,
                                         anon_permissions=[],
                                         public_permissions=[],
                                         owner=m.project_owner,
                                         blocked_code=project_choices.BLOCKED_BY_STAFF)

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

    return m


def test_modules_retrieve(client, data):
    public_url = reverse('projects-modules', kwargs={"pk": data.public_project.pk})
    private_url1 = reverse('projects-modules', kwargs={"pk": data.private_project1.pk})
    private_url2 = reverse('projects-modules', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-modules', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    results = helper_test_http_method(client, 'get', public_url, None, users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'get', private_url1, None, users)
    assert results == [401, 403, 403, 403, 200]
    results = helper_test_http_method(client, 'get', private_url2, None, users)
    assert results == [404, 404, 404, 403, 200]
    results = helper_test_http_method(client, 'get', blocked_url, None, users)
    assert results == [404, 404, 404, 403, 200]


def test_modules_update(client, data):
    public_url = reverse('projects-modules', kwargs={"pk": data.public_project.pk})
    private_url1 = reverse('projects-modules', kwargs={"pk": data.private_project1.pk})
    private_url2 = reverse('projects-modules', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-modules', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
        results = helper_test_http_method(client, 'put', public_url, {"att": "test"}, users)
        assert results == [405, 405, 405, 405, 405]

        results = helper_test_http_method(client, 'put', private_url1, {"att": "test"}, users)
        assert results == [405, 405, 405, 405, 405]

        results = helper_test_http_method(client, 'put', private_url2, {"att": "test"}, users)
        assert results == [405, 405, 405, 405, 405]

        results = helper_test_http_method(client, 'put', blocked_url, {"att": "test"}, users)
        assert results == [405, 405, 405, 405, 405]


def test_modules_delete(client, data):
    public_url = reverse('projects-modules', kwargs={"pk": data.public_project.pk})
    private_url1 = reverse('projects-modules', kwargs={"pk": data.private_project1.pk})
    private_url2 = reverse('projects-modules', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-modules', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
    ]

    results = helper_test_http_method(client, 'delete', public_url, None, users)
    assert results == [405, 405, 405, 405]
    results = helper_test_http_method(client, 'delete', private_url1, None, users)
    assert results == [405, 405, 405, 405]
    results = helper_test_http_method(client, 'delete', private_url2, None, users)
    assert results == [405, 405, 405, 405]
    results = helper_test_http_method(client, 'delete', blocked_url, None, users)
    assert results == [405, 405, 405, 405]


def test_modules_patch(client, data):
    public_url = reverse('projects-modules', kwargs={"pk": data.public_project.pk})
    private_url1 = reverse('projects-modules', kwargs={"pk": data.private_project1.pk})
    private_url2 = reverse('projects-modules', kwargs={"pk": data.private_project2.pk})
    blocked_url = reverse('projects-modules', kwargs={"pk": data.blocked_project.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            patch_data = json.dumps({"att": "test"})
            results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
            assert results == [401, 403, 403, 403, 204]

            patch_data = json.dumps({"att": "test"})
            results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
            assert results == [401, 403, 403, 403, 204]

            patch_data = json.dumps({"att": "test"})
            results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
            assert results == [404, 404, 404, 403, 204]

            patch_data = json.dumps({"att": "test"})
            results = helper_test_http_method(client, 'patch', blocked_url, patch_data, users)
            assert results == [404, 404, 404, 403, 451]
