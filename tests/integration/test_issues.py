import uuid
import csv

from unittest import mock

from django.core.urlresolvers import reverse

from taiga.projects.issues import services, models
from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_get_issues_from_bulk():
    data = """
Issue #1
Issue #2
"""
    issues = services.get_issues_from_bulk(data)

    assert len(issues) == 2
    assert issues[0].subject == "Issue #1"
    assert issues[1].subject == "Issue #2"


def test_create_issues_in_bulk(db):
    data = """
Issue #1
Issue #2
"""

    with mock.patch("taiga.projects.issues.services.db") as db:
        issues = services.create_issues_in_bulk(data)
        db.save_in_bulk.assert_called_once_with(issues, None, None)


def test_update_issues_order_in_bulk():
    data = [(1, 1), (2, 2)]

    with mock.patch("taiga.projects.issues.services.db") as db:
        services.update_issues_order_in_bulk(data)
        db.update_in_bulk_with_ids.assert_called_once_with([1, 2], [{"order": 1}, {"order": 2}],
                                                           model=models.Issue)


def test_create_issue_without_status(client):
    user = f.UserFactory.create()
    project = f.ProjectFactory.create(owner=user)
    status = f.IssueStatusFactory.create(project=project)
    priority = f.PriorityFactory.create(project=project)
    severity = f.SeverityFactory.create(project=project)
    type = f.IssueTypeFactory.create(project=project)
    project.default_issue_status = status
    project.default_priority = priority
    project.default_severity = severity
    project.default_issue_type = type
    project.save()
    f.MembershipFactory.create(project=project, user=user, is_owner=True)
    url = reverse("issues-list")

    data = {"subject": "Test user story", "project": project.id}
    client.login(user)
    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201
    assert response.data['status'] == project.default_issue_status.id
    assert response.data['severity'] == project.default_severity.id
    assert response.data['priority'] == project.default_priority.id
    assert response.data['type'] == project.default_issue_type.id


def test_api_create_issues_in_bulk(client):
    project = f.create_project()
    f.MembershipFactory(project=project, user=project.owner, is_owner=True)

    url = reverse("issues-bulk-create")

    data = {"bulk_issues": "Issue #1\nIssue #2\n",
            "project_id": project.id}

    client.login(project.owner)
    response = client.json.post(url, json.dumps(data))

    assert response.status_code == 200, response.data


def test_api_filter_by_subject(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="some random subject", owner=user)
    url = reverse("issues-list") + "?q=some subject"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1, number_of_issues


def test_api_filter_by_text_1(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=one"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_api_filter_by_text_2(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=this is the issue one"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_api_filter_by_text_3(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=this is the issue"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 2


def test_api_filter_by_text_4(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="this is the issue one", owner=user)
    f.create_issue(subject="this is the issue two", owner=issue.owner)
    url = reverse("issues-list") + "?q=one two"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 0


def test_api_filter_by_text_5(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="python 3", owner=user)
    url = reverse("issues-list") + "?q=python 3"

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_api_filter_by_text_6(client):
    user = f.UserFactory(is_superuser=True)
    f.create_issue(owner=user)
    issue = f.create_issue(subject="test", owner=user)
    issue.ref = 123
    issue.save()
    url = reverse("issues-list") + "?q=%s" % (issue.ref)

    client.login(issue.owner)
    response = client.get(url)
    number_of_issues = len(response.data)

    assert response.status_code == 200
    assert number_of_issues == 1


def test_get_invalid_csv(client):
    url = reverse("issues-csv")

    response = client.get(url)
    assert response.status_code == 404

    response = client.get("{}?uuid={}".format(url, "not-valid-uuid"))
    assert response.status_code == 404


def test_get_valid_csv(client):
    url = reverse("issues-csv")
    project = f.ProjectFactory.create(issues_csv_uuid=uuid.uuid4().hex)

    response = client.get("{}?uuid={}".format(url, project.issues_csv_uuid))
    assert response.status_code == 200


def test_custom_fields_csv_generation():
    project = f.ProjectFactory.create(issues_csv_uuid=uuid.uuid4().hex)
    attr = f.IssueCustomAttributeFactory.create(project=project, name="attr1", description="desc")
    issue = f.IssueFactory.create(project=project)
    attr_values = issue.custom_attributes_values
    attr_values.attributes_values = {str(attr.id):"val1"}
    attr_values.save()
    queryset = project.issues.all()
    data = services.issues_to_csv(project, queryset)
    data.seek(0)
    reader = csv.reader(data)
    row = next(reader)
    assert row[16] == attr.name
    row = next(reader)
    assert row[16] == "val1"
