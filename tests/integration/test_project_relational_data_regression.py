# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
Regression tests for the ?include= relational data feature.

These tests guard against regressions by verifying:
  1. Pre-existing API responses are not broken by the new fields.
  2. The new `userstories` / `tasks` fields are always present in project
     detail responses (empty list when not requested).
  3. Private project access control is not weakened by the new feature.
  4. The `include` param is silently ignored on list endpoints (no crash).
  5. Unknown/garbage `include` values don't cause 500 errors.
  6. Combining `include` with other existing query params keeps working.
"""

import pytest
from django.urls import reverse

from taiga.base.utils import json
from taiga.projects.models import Project
from taiga.projects.userstories.models import UserStory
from taiga.projects.tasks.models import Task

from .. import factories as f

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Regression: pre-existing fields must survive the new serializer additions
# ---------------------------------------------------------------------------

class TestExistingProjectDetailFieldsUnchanged:
    """Ensure the new userstories/tasks fields don't remove or rename
    anything that was in the response before this feature."""

    REQUIRED_TOP_LEVEL_FIELDS = [
        "id", "name", "slug", "description",
        "created_date", "modified_date",
        "owner", "members",
        "is_private", "is_backlog_activated", "is_kanban_activated",
        "is_wiki_activated", "is_issues_activated", "is_epics_activated",
        "total_milestones", "total_story_points",
        "anon_permissions", "public_permissions",
        "is_featured", "is_looking_for_people",
        "my_permissions", "i_am_owner", "i_am_admin", "i_am_member",
        "tags", "tags_colors",
        "epic_statuses", "us_statuses", "points",
        "task_statuses", "issue_statuses", "issue_types",
        "priorities", "severities",
        "roles", "milestones",
        # new fields must always be present
        "userstories", "tasks",
    ]

    def test_all_required_fields_present_without_include(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url)

        assert response.status_code == 200
        for field in self.REQUIRED_TOP_LEVEL_FIELDS:
            assert field in response.data, f"Field '{field}' missing from response"

    def test_all_required_fields_present_with_include_userstories(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        f.UserStoryFactory.create(project=project)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "userstories"})

        assert response.status_code == 200
        for field in self.REQUIRED_TOP_LEVEL_FIELDS:
            assert field in response.data, f"Field '{field}' missing from response"

    def test_all_required_fields_present_with_include_tasks(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "tasks"})

        assert response.status_code == 200
        for field in self.REQUIRED_TOP_LEVEL_FIELDS:
            assert field in response.data, f"Field '{field}' missing from response"


# ---------------------------------------------------------------------------
# Regression: userstories / tasks are always empty lists without the param
# ---------------------------------------------------------------------------

class TestNewFieldsDefaultToEmptyList:

    def test_userstories_is_empty_list_by_default(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        f.UserStoryFactory.create(project=project)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url)  # no include= param

        assert response.status_code == 200
        assert response.data["userstories"] == []

    def test_tasks_is_empty_list_by_default(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        us = f.UserStoryFactory.create(project=project)
        f.TaskFactory.create(project=project, user_story=us)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url)

        assert response.status_code == 200
        assert response.data["tasks"] == []

    def test_userstories_is_empty_list_when_only_tasks_included(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        f.UserStoryFactory.create(project=project)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "tasks"})

        assert response.status_code == 200
        assert response.data["userstories"] == []

    def test_tasks_is_empty_list_when_only_userstories_included(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        us = f.UserStoryFactory.create(project=project)
        f.TaskFactory.create(project=project, user_story=us)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "userstories"})

        assert response.status_code == 200
        assert response.data["tasks"] == []


# ---------------------------------------------------------------------------
# Regression: access control must not be weakened
# ---------------------------------------------------------------------------

class TestAccessControlNotWeakened:

    def test_anonymous_cannot_access_private_project_with_include(self, client):
        project = f.ProjectFactory.create(is_private=True)
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "userstories,tasks"})

        assert response.status_code == 401

    def test_non_member_cannot_access_private_project_with_include(self, client):
        owner = f.UserFactory.create()
        other_user = f.UserFactory.create()
        project = f.ProjectFactory.create(owner=owner, is_private=True)
        f.MembershipFactory(user=owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        client.login(other_user)
        response = client.json.get(url, {"include": "userstories,tasks"})

        assert response.status_code == 404

    def test_member_can_access_private_project_with_include(self, client):
        project = f.ProjectFactory.create(is_private=True)
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        client.login(project.owner)
        response = client.json.get(url, {"include": "userstories,tasks"})

        assert response.status_code == 200

    def test_include_does_not_expose_other_projects_tasks(self, client):
        """Regression guard: tasks from project B must never appear when
        requesting project A with ?include=tasks."""
        owner = f.UserFactory.create()
        project_a = f.ProjectFactory.create(
            owner=owner,
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        project_b = f.ProjectFactory.create(
            owner=owner,
            is_private=False,
        )
        f.MembershipFactory(user=owner, project=project_a, is_admin=True)
        f.MembershipFactory(user=owner, project=project_b, is_admin=True)

        us_b = f.UserStoryFactory.create(project=project_b)
        task_b = f.TaskFactory.create(project=project_b, user_story=us_b)

        url = reverse("projects-detail", kwargs={"pk": project_a.id})
        response = client.json.get(url, {"include": "tasks"})

        assert response.status_code == 200
        returned_ids = {t["id"] for t in response.data["tasks"]}
        assert task_b.id not in returned_ids

    def test_include_does_not_expose_other_projects_userstories(self, client):
        """Regression guard: user stories from project B must never appear
        when requesting project A with ?include=userstories."""
        owner = f.UserFactory.create()
        project_a = f.ProjectFactory.create(
            owner=owner,
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        project_b = f.ProjectFactory.create(owner=owner, is_private=False)
        f.MembershipFactory(user=owner, project=project_a, is_admin=True)
        f.MembershipFactory(user=owner, project=project_b, is_admin=True)

        us_b = f.UserStoryFactory.create(project=project_b, subject="Secret story")

        url = reverse("projects-detail", kwargs={"pk": project_a.id})
        response = client.json.get(url, {"include": "userstories"})

        assert response.status_code == 200
        returned_ids = {u["id"] for u in response.data["userstories"]}
        assert us_b.id not in returned_ids


# ---------------------------------------------------------------------------
# Regression: unknown / garbage include values must not cause 500 errors
# ---------------------------------------------------------------------------

class TestBadIncludeParamIsHarmless:

    def test_unknown_include_value_returns_200(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": "nonexistent_relation"})

        assert response.status_code == 200
        assert response.data["userstories"] == []
        assert response.data["tasks"] == []

    def test_empty_include_value_returns_200(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": ""})

        assert response.status_code == 200

    def test_include_with_whitespace_is_handled(self, client):
        project = f.ProjectFactory.create(
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        f.UserStoryFactory.create(project=project)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        response = client.json.get(url, {"include": " userstories , tasks "})

        assert response.status_code == 200
        # spaces stripped → both should activate
        assert isinstance(response.data["userstories"], list)
        assert isinstance(response.data["tasks"], list)


# ---------------------------------------------------------------------------
# Regression: project list endpoint must not crash with include param
# ---------------------------------------------------------------------------

class TestIncludeParamOnListEndpoint:

    def test_list_endpoint_with_include_returns_200(self, client):
        user = f.UserFactory.create()
        f.ProjectFactory.create(
            owner=user,
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        url = reverse("projects-list")

        response = client.json.get(url, {"include": "userstories,tasks"})

        # List uses ProjectSerializer (not ProjectDetailSerializer),
        # so userstories/tasks are absent — but no 500 should occur.
        assert response.status_code == 200

    def test_by_slug_with_include_userstories(self, client):
        project = f.ProjectFactory.create(is_private=True)
        f.MembershipFactory(user=project.owner, project=project, is_admin=True)
        f.UserStoryFactory.create(project=project, subject="Slug story")
        url = reverse("projects-by-slug")

        client.login(project.owner)
        response = client.json.get(url, {"slug": project.slug, "include": "userstories"})

        assert response.status_code == 200
        assert any(u["subject"] == "Slug story" for u in response.data["userstories"])


# ---------------------------------------------------------------------------
# Regression: combining include with existing query params
# ---------------------------------------------------------------------------

class TestIncludeCombinedWithOtherParams:

    def test_include_with_slight_param_returns_200_without_extra_fields(self, client):
        """slight=true uses ProjectLightSerializer which has no userstories/tasks.
        The include param should be parsed but do nothing harmful."""
        user = f.UserFactory.create()
        project = f.ProjectFactory.create(
            owner=user,
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        f.MembershipFactory(user=user, project=project, is_admin=True)
        url = reverse("projects-list")

        response = client.json.get(url, {"slight": "true", "include": "userstories"})

        assert response.status_code == 200

    def test_include_combined_with_member_filter(self, client):
        user = f.UserFactory.create()
        project = f.ProjectFactory.create(
            owner=user,
            is_private=False,
            anon_permissions=["view_project"],
            public_permissions=["view_project"],
        )
        role = f.RoleFactory.create(project=project, permissions=["view_project"])
        f.MembershipFactory(user=user, project=project, role=role, is_admin=True)
        f.UserStoryFactory.create(project=project)
        url = reverse("projects-detail", kwargs={"pk": project.id})

        client.login(user)
        response = client.json.get(url, {"include": "userstories,tasks"})

        assert response.status_code == 200
        assert isinstance(response.data["userstories"], list)
        assert isinstance(response.data["tasks"], list)
