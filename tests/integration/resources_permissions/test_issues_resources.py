import uuid

from django.core.urlresolvers import reverse

from taiga.projects.issues.serializers import IssueSerializer
from taiga.permissions.permissions import MEMBERS_PERMISSIONS, ANON_PERMISSIONS, USER_PERMISSIONS
from taiga.base.utils import json

from tests import factories as f
from tests.utils import helper_test_http_method, disconnect_signals, reconnect_signals
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
                                        owner=m.project_owner,
                                        issues_csv_uuid=uuid.uuid4().hex)
    m.private_project1 = f.ProjectFactory(is_private=True,
                                          anon_permissions=list(map(lambda x: x[0], ANON_PERMISSIONS)),
                                          public_permissions=list(map(lambda x: x[0], USER_PERMISSIONS)),
                                          owner=m.project_owner,
                                          issues_csv_uuid=uuid.uuid4().hex)
    m.private_project2 = f.ProjectFactory(is_private=True,
                                          anon_permissions=[],
                                          public_permissions=[],
                                          owner=m.project_owner,
                                          issues_csv_uuid=uuid.uuid4().hex)

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


def test_issue_retrieve(client, data):
    public_url = reverse('issues-detail', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-detail', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-detail', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_update(client, data):
    public_url = reverse('issues-detail', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-detail', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-detail', kwargs={"pk": data.private_issue2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            issue_data = IssueSerializer(data.public_issue).data
            issue_data["subject"] = "test"
            issue_data = json.dumps(issue_data)
            results = helper_test_http_method(client, 'put', public_url, issue_data, users)
            assert results == [401, 403, 403, 200, 200]

            issue_data = IssueSerializer(data.private_issue1).data
            issue_data["subject"] = "test"
            issue_data = json.dumps(issue_data)
            results = helper_test_http_method(client, 'put', private_url1, issue_data, users)
            assert results == [401, 403, 403, 200, 200]

            issue_data = IssueSerializer(data.private_issue2).data
            issue_data["subject"] = "test"
            issue_data = json.dumps(issue_data)
            results = helper_test_http_method(client, 'put', private_url2, issue_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_issue_update_with_project_change(client):
    user1 = f.UserFactory.create()
    user2 = f.UserFactory.create()
    user3 = f.UserFactory.create()
    user4 = f.UserFactory.create()
    project1 = f.ProjectFactory()
    project2 = f.ProjectFactory()

    issue_status1 = f.IssueStatusFactory.create(project=project1)
    issue_status2 = f.IssueStatusFactory.create(project=project2)

    priority1 = f.PriorityFactory.create(project=project1)
    priority2 = f.PriorityFactory.create(project=project2)

    severity1 = f.SeverityFactory.create(project=project1)
    severity2 = f.SeverityFactory.create(project=project2)

    issue_type1 = f.IssueTypeFactory.create(project=project1)
    issue_type2 = f.IssueTypeFactory.create(project=project2)

    project1.default_issue_status = issue_status1
    project2.default_issue_status = issue_status2

    project1.default_priority = priority1
    project2.default_priority = priority2

    project1.default_severity = severity1
    project2.default_severity = severity2

    project1.default_issue_type = issue_type1
    project2.default_issue_type = issue_type2

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

    issue = f.IssueFactory.create(project=project1)

    url = reverse('issues-detail', kwargs={"pk": issue.pk})

    # Test user with permissions in both projects
    client.login(user1)

    issue_data = IssueSerializer(issue).data
    issue_data["project"] = project2.id
    issue_data = json.dumps(issue_data)

    response = client.put(url, data=issue_data, content_type="application/json")

    assert response.status_code == 200

    issue.project = project1
    issue.save()

    # Test user with permissions in only origin project
    client.login(user2)

    issue_data = IssueSerializer(issue).data
    issue_data["project"] = project2.id
    issue_data = json.dumps(issue_data)

    response = client.put(url, data=issue_data, content_type="application/json")

    assert response.status_code == 403

    issue.project = project1
    issue.save()

    # Test user with permissions in only destionation project
    client.login(user3)

    issue_data = IssueSerializer(issue).data
    issue_data["project"] = project2.id
    issue_data = json.dumps(issue_data)

    response = client.put(url, data=issue_data, content_type="application/json")

    assert response.status_code == 403

    issue.project = project1
    issue.save()

    # Test user without permissions in the projects
    client.login(user4)

    issue_data = IssueSerializer(issue).data
    issue_data["project"] = project2.id
    issue_data = json.dumps(issue_data)

    response = client.put(url, data=issue_data, content_type="application/json")

    assert response.status_code == 403

    issue.project = project1
    issue.save()


def test_issue_delete(client, data):
    public_url = reverse('issues-detail', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-detail', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-detail', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_list(client, data):
    url = reverse('issues-list')

    response = client.get(url)
    issues_data = json.loads(response.content.decode('utf-8'))
    assert len(issues_data) == 2
    assert response.status_code == 200

    client.login(data.registered_user)

    response = client.get(url)
    issues_data = json.loads(response.content.decode('utf-8'))
    assert len(issues_data) == 2
    assert response.status_code == 200

    client.login(data.project_member_with_perms)

    response = client.get(url)
    issues_data = json.loads(response.content.decode('utf-8'))
    assert len(issues_data) == 3
    assert response.status_code == 200

    client.login(data.project_owner)

    response = client.get(url)
    issues_data = json.loads(response.content.decode('utf-8'))
    assert len(issues_data) == 3
    assert response.status_code == 200


def test_issue_list_filter_by_project_ok(client, data):
    url = "{}?project={}".format(reverse("issues-list"), data.public_project.pk)

    client.login(data.project_owner)
    response = client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 1


def test_issue_list_filter_by_project_error(client, data):
    url = "{}?project={}".format(reverse("issues-list"), "-ERROR-")

    client.login(data.project_owner)
    response = client.get(url)

    assert response.status_code == 400


def test_issue_create(client, data):
    url = reverse('issues-list')

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
        "severity": data.public_project.severities.all()[0].pk,
        "priority": data.public_project.priorities.all()[0].pk,
        "status": data.public_project.issue_statuses.all()[0].pk,
        "type": data.public_project.issue_types.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 2,
        "project": data.private_project1.pk,
        "severity": data.private_project1.severities.all()[0].pk,
        "priority": data.private_project1.priorities.all()[0].pk,
        "status": data.private_project1.issue_statuses.all()[0].pk,
        "type": data.private_project1.issue_types.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 201, 201, 201, 201]

    create_data = json.dumps({
        "subject": "test",
        "ref": 3,
        "project": data.private_project2.pk,
        "severity": data.private_project2.severities.all()[0].pk,
        "priority": data.private_project2.priorities.all()[0].pk,
        "status": data.private_project2.issue_statuses.all()[0].pk,
        "type": data.private_project2.issue_types.all()[0].pk,
    })
    results = helper_test_http_method(client, 'post', url, create_data, users)
    assert results == [401, 403, 403, 201, 201]


def test_issue_patch(client, data):
    public_url = reverse('issues-detail', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-detail', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-detail', kwargs={"pk": data.private_issue2.pk})

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    with mock.patch.object(OCCResourceMixin, "_validate_and_update_version"):
            patch_data = json.dumps({"subject": "test", "version": data.public_issue.version})
            results = helper_test_http_method(client, 'patch', public_url, patch_data, users)
            assert results == [401, 403, 403, 200, 200]

            patch_data = json.dumps({"subject": "test", "version": data.private_issue1.version})
            results = helper_test_http_method(client, 'patch', private_url1, patch_data, users)
            assert results == [401, 403, 403, 200, 200]

            patch_data = json.dumps({"subject": "test", "version": data.private_issue2.version})
            results = helper_test_http_method(client, 'patch', private_url2, patch_data, users)
            assert results == [401, 403, 403, 200, 200]


def test_issue_bulk_create(client, data):
    data.public_issue.project.default_issue_status = f.IssueStatusFactory()
    data.public_issue.project.default_issue_type = f.IssueTypeFactory()
    data.public_issue.project.default_priority = f.PriorityFactory()
    data.public_issue.project.default_severity = f.SeverityFactory()
    data.public_issue.project.save()

    data.private_issue1.project.default_issue_status = f.IssueStatusFactory()
    data.private_issue1.project.default_issue_type = f.IssueTypeFactory()
    data.private_issue1.project.default_priority = f.PriorityFactory()
    data.private_issue1.project.default_severity = f.SeverityFactory()
    data.private_issue1.project.save()

    data.private_issue2.project.default_issue_status = f.IssueStatusFactory()
    data.private_issue2.project.default_issue_type = f.IssueTypeFactory()
    data.private_issue2.project.default_priority = f.PriorityFactory()
    data.private_issue2.project.default_severity = f.SeverityFactory()
    data.private_issue2.project.save()

    url = reverse('issues-bulk-create')

    users = [
        None,
        data.registered_user,
        data.project_member_without_perms,
        data.project_member_with_perms,
        data.project_owner
    ]

    bulk_data = json.dumps({"bulk_issues": "test1\ntest2",
                            "project_id": data.public_issue.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 200, 200, 200, 200]

    bulk_data = json.dumps({"bulk_issues": "test1\ntest2",
                            "project_id": data.private_issue1.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 200, 200, 200, 200]

    bulk_data = json.dumps({"bulk_issues": "test1\ntest2",
                            "project_id": data.private_issue2.project.pk})
    results = helper_test_http_method(client, 'post', url, bulk_data, users)
    assert results == [401, 403, 403, 200, 200]


def test_issue_action_upvote(client, data):
    public_url = reverse('issues-upvote', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-upvote', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-upvote', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_action_downvote(client, data):
    public_url = reverse('issues-downvote', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-downvote', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-downvote', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_voters_list(client, data):
    public_url = reverse('issue-voters-list', kwargs={"resource_id": data.public_issue.pk})
    private_url1 = reverse('issue-voters-list', kwargs={"resource_id": data.private_issue1.pk})
    private_url2 = reverse('issue-voters-list', kwargs={"resource_id": data.private_issue2.pk})

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


def test_issue_voters_retrieve(client, data):
    add_vote(data.public_issue, data.project_owner)
    public_url = reverse('issue-voters-detail', kwargs={"resource_id": data.public_issue.pk,
                                                        "pk": data.project_owner.pk})
    add_vote(data.private_issue1, data.project_owner)
    private_url1 = reverse('issue-voters-detail', kwargs={"resource_id": data.private_issue1.pk,
                                                          "pk": data.project_owner.pk})
    add_vote(data.private_issue2, data.project_owner)
    private_url2 = reverse('issue-voters-detail', kwargs={"resource_id": data.private_issue2.pk,
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


def test_issues_csv(client, data):
    url = reverse('issues-csv')
    csv_public_uuid = data.public_project.issues_csv_uuid
    csv_private1_uuid = data.private_project1.issues_csv_uuid
    csv_private2_uuid = data.private_project1.issues_csv_uuid

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


def test_issue_action_watch(client, data):
    public_url = reverse('issues-watch', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-watch', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-watch', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_action_unwatch(client, data):
    public_url = reverse('issues-unwatch', kwargs={"pk": data.public_issue.pk})
    private_url1 = reverse('issues-unwatch', kwargs={"pk": data.private_issue1.pk})
    private_url2 = reverse('issues-unwatch', kwargs={"pk": data.private_issue2.pk})

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


def test_issue_watchers_list(client, data):
    public_url = reverse('issue-watchers-list', kwargs={"resource_id": data.public_issue.pk})
    private_url1 = reverse('issue-watchers-list', kwargs={"resource_id": data.private_issue1.pk})
    private_url2 = reverse('issue-watchers-list', kwargs={"resource_id": data.private_issue2.pk})

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


def test_issue_watchers_retrieve(client, data):
    add_watcher(data.public_issue, data.project_owner)
    public_url = reverse('issue-watchers-detail', kwargs={"resource_id": data.public_issue.pk,
                                                        "pk": data.project_owner.pk})
    add_watcher(data.private_issue1, data.project_owner)
    private_url1 = reverse('issue-watchers-detail', kwargs={"resource_id": data.private_issue1.pk,
                                                          "pk": data.project_owner.pk})
    add_watcher(data.private_issue2, data.project_owner)
    private_url2 = reverse('issue-watchers-detail', kwargs={"resource_id": data.private_issue2.pk,
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
