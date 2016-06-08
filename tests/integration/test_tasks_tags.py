# -*- coding: utf-8 -*-
from unittest import mock
from collections import OrderedDict

from django.core.urlresolvers import reverse

from taiga.base.utils import json

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_api_task_add_new_tags_with_error(client):
    project = f.ProjectFactory.create()
    task = f.create_task(project=project, status__project=project, milestone=None, user_story=None)
    f.MembershipFactory.create(project=project, user=task.owner, is_admin=True)
    url = reverse("tasks-detail", kwargs={"pk": task.pk})
    data = {
        "tags": [],
        "version": task.version
    }

    client.login(task.owner)

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


def test_api_task_add_new_tags_without_colors(client):
    project = f.ProjectFactory.create()
    task = f.create_task(project=project, status__project=project, milestone=None, user_story=None)
    f.MembershipFactory.create(project=project, user=task.owner, is_admin=True)
    url = reverse("tasks-detail", kwargs={"pk": task.pk})
    data = {
        "tags": [
            ["back", None],
            ["front", None],
            ["ux", None]
        ],
        "version": task.version
    }

    client.login(task.owner)

    response = client.json.patch(url, json.dumps(data))

    assert response.status_code == 200, response.data

    tags_colors = OrderedDict(project.tags_colors)
    assert not tags_colors.keys()

    project.refresh_from_db()

    tags_colors = OrderedDict(project.tags_colors)
    assert "back" in tags_colors and "front" in tags_colors and "ux" in tags_colors


def test_api_task_add_new_tags_with_colors(client):
    project = f.ProjectFactory.create()
    task = f.create_task(project=project, status__project=project, milestone=None, user_story=None)
    f.MembershipFactory.create(project=project, user=task.owner, is_admin=True)
    url = reverse("tasks-detail", kwargs={"pk": task.pk})
    data = {
        "tags": [
            ["back", "#fff8e7"],
            ["front", None],
            ["ux", "#fabada"]
        ],
        "version": task.version
    }

    client.login(task.owner)

    response = client.json.patch(url, json.dumps(data))
    assert response.status_code == 200, response.data

    tags_colors = OrderedDict(project.tags_colors)
    assert not tags_colors.keys()

    project.refresh_from_db()

    tags_colors = OrderedDict(project.tags_colors)
    assert "back" in tags_colors and "front" in tags_colors and "ux" in tags_colors
    assert tags_colors["back"] == "#fff8e7"
    assert tags_colors["ux"] == "#fabada"


def test_api_create_new_task_with_tags(client):
    project = f.ProjectFactory.create()
    status = f.TaskStatusFactory.create(project=project)
    project.default_task_status = status
    project.save()
    f.MembershipFactory.create(project=project, user=project.owner, is_admin=True)
    url = reverse("tasks-list")

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
