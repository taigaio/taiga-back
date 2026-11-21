# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import connection

from .. import factories as f

import pytest
pytestmark = pytest.mark.django_db


def test_json_object_delete_keys_has_no_keyword_parameter_name():
    # A parameter called "json" is dumped unquoted by pg_dump 16 and rejected
    # when the dump is restored on PostgreSQL 18.
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT pg_get_function_identity_arguments(oid), proargnames::text[]
              FROM pg_proc
             WHERE proname = 'json_object_delete_keys'
          ORDER BY 1
        """)
        rows = cursor.fetchall()

    assert len(rows) == 2
    for _, argnames in rows:
        assert "json" not in argnames


@pytest.mark.parametrize("cast, value", [
    ("json", '{"a": 1, "b": "x", "c": [1, 2]}'),
    ("jsonb", '{"a": 1, "b": "x", "c": [1, 2]}'),
])
def test_json_object_delete_keys_removes_keys(cast, value):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT json_object_delete_keys(%s::" + cast + ", 'a', 'c')::text",
            [value])
        (result,) = cursor.fetchone()

    assert result.replace(" ", "") == '{"b":"x"}'


def test_json_object_delete_keys_on_empty_result():
    with connection.cursor() as cursor:
        cursor.execute("SELECT json_object_delete_keys('{\"a\": 1}'::jsonb, 'a')::text")
        (result,) = cursor.fetchone()

    assert result == "{}"


def test_delete_custom_attribute_removes_key_from_values():
    attr = f.UserStoryCustomAttributeFactory()
    story = f.UserStoryFactory(project=attr.project)
    other_key = "99999"
    values = story.custom_attributes_values
    values.attributes_values = {str(attr.id): "gone", other_key: "stay"}
    values.save()

    attr.delete()
    values.refresh_from_db()

    assert values.attributes_values == {other_key: "stay"}
