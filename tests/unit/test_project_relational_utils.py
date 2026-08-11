# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
Unit tests for the relational data utilities:
  taiga.projects.utils.attach_userstories_to_project
  taiga.projects.utils.attach_tasks_to_project

and the ProjectDetailSerializer methods:
  get_userstories
  get_tasks

Each test isolates a single function or method, using mocks or minimal db
objects only as needed.
"""

import pytest
from unittest import mock

from taiga.projects.utils import attach_userstories_to_project, attach_tasks_to_project
from taiga.projects.serializers import ProjectDetailSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_queryset_mock(model_db_table="projects_project"):
    """Return a mock queryset whose .model._meta.db_table is predictable."""
    qs = mock.MagicMock()
    qs.model._meta.db_table = model_db_table
    # .extra(select=...) must return the same mock so callers can chain
    qs.extra.return_value = qs
    return qs


# ---------------------------------------------------------------------------
# Unit tests: attach_userstories_to_project
# ---------------------------------------------------------------------------

class TestAttachUserstoriesToProject:
    def test_returns_queryset(self):
        qs = _make_queryset_mock()
        result = attach_userstories_to_project(qs)
        assert result is qs

    def test_calls_extra_with_userstories_attr_key(self):
        qs = _make_queryset_mock()
        attach_userstories_to_project(qs)
        qs.extra.assert_called_once()
        call_kwargs = qs.extra.call_args
        select_dict = call_kwargs[1].get("select") or call_kwargs[0][0]
        assert "userstories_attr" in select_dict

    def test_custom_as_field_name_is_used(self):
        qs = _make_queryset_mock()
        attach_userstories_to_project(qs, as_field="custom_us")
        select_dict = qs.extra.call_args[1]["select"]
        assert "custom_us" in select_dict

    def test_sql_references_userstories_table(self):
        qs = _make_queryset_mock()
        attach_userstories_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["userstories_attr"]
        assert "userstories_userstory" in sql

    def test_sql_filters_by_project_id(self):
        qs = _make_queryset_mock("projects_project")
        attach_userstories_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["userstories_attr"]
        assert "projects_project.id" in sql

    def test_sql_contains_required_columns(self):
        qs = _make_queryset_mock()
        attach_userstories_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["userstories_attr"]
        for col in ("ref", "subject", "status_id", "is_closed", "backlog_order",
                    "sprint_order", "kanban_order", "milestone_id",
                    "assigned_to_id", "is_blocked"):
            assert col in sql, f"Expected column '{col}' in SQL"

    def test_sql_uses_correct_db_table_name(self):
        qs = _make_queryset_mock("custom_schema_project")
        attach_userstories_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["userstories_attr"]
        assert "custom_schema_project.id" in sql


# ---------------------------------------------------------------------------
# Unit tests: attach_tasks_to_project
# ---------------------------------------------------------------------------

class TestAttachTasksToProject:
    def test_returns_queryset(self):
        qs = _make_queryset_mock()
        result = attach_tasks_to_project(qs)
        assert result is qs

    def test_calls_extra_with_tasks_attr_key(self):
        qs = _make_queryset_mock()
        attach_tasks_to_project(qs)
        qs.extra.assert_called_once()
        select_dict = qs.extra.call_args[1]["select"]
        assert "tasks_attr" in select_dict

    def test_custom_as_field_name_is_used(self):
        qs = _make_queryset_mock()
        attach_tasks_to_project(qs, as_field="my_tasks")
        select_dict = qs.extra.call_args[1]["select"]
        assert "my_tasks" in select_dict

    def test_sql_references_tasks_table(self):
        qs = _make_queryset_mock()
        attach_tasks_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["tasks_attr"]
        assert "tasks_task" in sql

    def test_sql_joins_taskstatus_for_is_closed(self):
        qs = _make_queryset_mock()
        attach_tasks_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["tasks_attr"]
        assert "projects_taskstatus" in sql
        assert "is_closed" in sql

    def test_sql_filters_by_project_id(self):
        qs = _make_queryset_mock("projects_project")
        attach_tasks_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["tasks_attr"]
        assert "projects_project.id" in sql

    def test_sql_contains_required_columns(self):
        qs = _make_queryset_mock()
        attach_tasks_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["tasks_attr"]
        for col in ("ref", "subject", "status_id", "is_blocked",
                    "is_iocaine", "user_story_id", "milestone_id",
                    "assigned_to_id"):
            assert col in sql, f"Expected column '{col}' in SQL"

    def test_sql_uses_correct_db_table_name(self):
        qs = _make_queryset_mock("other_schema_project")
        attach_tasks_to_project(qs)
        sql = qs.extra.call_args[1]["select"]["tasks_attr"]
        assert "other_schema_project.id" in sql


# ---------------------------------------------------------------------------
# Unit tests: ProjectDetailSerializer.get_userstories / get_tasks
# ---------------------------------------------------------------------------

class TestProjectDetailSerializerGetUserstories:
    def _make_obj(self, include=False, attr=None):
        obj = mock.MagicMock()
        obj.include_userstories = include
        obj.userstories_attr = attr
        return obj

    def test_returns_empty_list_when_include_flag_not_set(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=False)
        assert serializer.get_userstories(obj) == []

    def test_returns_empty_list_when_include_flag_is_false(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=False, attr=[{"id": 1}])
        assert serializer.get_userstories(obj) == []

    def test_returns_attr_when_include_flag_is_true(self):
        serializer = ProjectDetailSerializer()
        data = [{"id": 1, "subject": "Story"}, {"id": 2, "subject": "Story 2"}]
        obj = self._make_obj(include=True, attr=data)
        assert serializer.get_userstories(obj) == data

    def test_returns_empty_list_when_attr_is_none_even_with_include(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=True, attr=None)
        assert serializer.get_userstories(obj) == []

    def test_raises_assertion_when_include_set_but_attr_missing(self):
        serializer = ProjectDetailSerializer()
        obj = mock.MagicMock(spec=[])          # no userstories_attr at all
        obj.include_userstories = True
        with pytest.raises(AssertionError):
            serializer.get_userstories(obj)


class TestProjectDetailSerializerGetTasks:
    def _make_obj(self, include=False, attr=None):
        obj = mock.MagicMock()
        obj.include_tasks = include
        obj.tasks_attr = attr
        return obj

    def test_returns_empty_list_when_include_flag_not_set(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=False)
        assert serializer.get_tasks(obj) == []

    def test_returns_empty_list_when_include_flag_is_false(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=False, attr=[{"id": 10}])
        assert serializer.get_tasks(obj) == []

    def test_returns_attr_when_include_flag_is_true(self):
        serializer = ProjectDetailSerializer()
        data = [{"id": 10, "subject": "Task A"}, {"id": 11, "subject": "Task B"}]
        obj = self._make_obj(include=True, attr=data)
        assert serializer.get_tasks(obj) == data

    def test_returns_empty_list_when_attr_is_none_even_with_include(self):
        serializer = ProjectDetailSerializer()
        obj = self._make_obj(include=True, attr=None)
        assert serializer.get_tasks(obj) == []

    def test_raises_assertion_when_include_set_but_attr_missing(self):
        serializer = ProjectDetailSerializer()
        obj = mock.MagicMock(spec=[])
        obj.include_tasks = True
        with pytest.raises(AssertionError):
            serializer.get_tasks(obj)
