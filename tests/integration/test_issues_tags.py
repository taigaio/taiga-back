# -*- coding: utf-8 -*-
from unittest import mock
from collections import OrderedDict

from django.core.urlresolvers import reverse

from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_api_issue_add_new_tags_with_error(client):
    project = f.ProjectFactory.create()
    issue = f.create_issue(project=project, status__project=project)
    f.MembershipFactory.create(project=project, user=issue.owner, is_admin=True)
    url = reverse("issues-detail", kwargs={"pk": issue.pk})
    data = {
        "tags": [],
        "version": issue.version
    }

    client.login(issue.owner)

    data["tags"] = [1]
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "tags" in response.data

    data["tags"] = [["back"]]
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "tags" in response.data

    data["tags"] = [["back", "#cccc"]]
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "tags" in response.data

    data["tags"] = [[1, "#ccc"]]
    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 400, response.data
    assert "tags" in response.data


def test_api_issue_add_new_tags_without_colors(client):
    project = f.ProjectFactory.create()
    issue = f.create_issue(project=project, status__project=project)
    f.MembershipFactory.create(project=project, user=issue.owner, is_admin=True)
    url = reverse("issues-detail", kwargs={"pk": issue.pk})
    data = {
        "tags": [
            ["back", None],
            ["front", None],
            ["ux", None]
        ],
        "version": issue.version
    }

    client.login(issue.owner)

    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200, response.data

    tags_colors = OrderedDict(project.tags_colors)
    assert not tags_colors.keys()

    project.refresh_from_db()

    tags_colors = OrderedDict(project.tags_colors)
    assert "back" in tags_colors and "front" in tags_colors and "ux" in tags_colors


def test_api_issue_add_new_tags_with_colors(client):
    project = f.ProjectFactory.create()
    issue = f.create_issue(project=project, status__project=project)
    f.MembershipFactory.create(project=project, user=issue.owner, is_admin=True)
    url = reverse("issues-detail", kwargs={"pk": issue.pk})
    data = {
        "tags": [
            ["back", "#fff8e7"],
            ["front", None],
            ["ux", "#fabada"]
        ],
        "version": issue.version
    }

    client.login(issue.owner)

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    tags_colors = OrderedDict(project.tags_colors)
    assert not tags_colors.keys()

    project.refresh_from_db()

    tags_colors = OrderedDict(project.tags_colors)
    assert "back" in tags_colors and "front" in tags_colors and "ux" in tags_colors
    assert tags_colors["back"] == "#fff8e7"
    assert tags_colors["ux"] == "#fabada"


def test_api_create_new_issue_with_tags(client):
    project = f.ProjectFactory.create()
    status = f.IssueStatusFactory.create(project=project)
    project.default_issue_status = status
    project.save()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    url = reverse("issues-list")

    data = {
        "subject": "Test user story",
        "project": project.id,
        "tags": [
            ["back", "#fff8e7"],
            ["front", None],
            ["ux", "#fabada"]
        ]
    }

    client.login(project.owner)

    response = client.json.post(url, json.dumps(data))
    assert response.status_code == 201, response.data

    assert ("back" in response.data["tags"] and
            "front" in response.data["tags"] and
            "ux" in response.data["tags"])

    tags_colors = OrderedDict(project.tags_colors)
    assert not tags_colors.keys()

    project.refresh_from_db()

    tags_colors = OrderedDict(project.tags_colors)
    assert "back" in tags_colors and "front" in tags_colors and "ux" in tags_colors
    assert tags_colors["back"] == "#fff8e7"
    assert tags_colors["ux"] == "#fabada"
