# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import pytest

from django.db import connection

from taiga.projects.services import bulk_update_order as bulk_order
from taiga.searches import services as search_services

from .. import factories as f

pytestmark = pytest.mark.django_db


# Same expression as projects_project_textquery_idx (projects migration 0057)
# and taiga.projects.filters.QFilterBackend.
PROJECT_TSVECTOR = """
    setweight(to_tsvector('simple',
              coalesce(projects_project.name, '')), 'A') ||
    setweight(to_tsvector('simple',
              coalesce(inmutable_array_to_string(projects_project.tags), '')), 'B') ||
    setweight(to_tsvector('simple',
              coalesce(projects_project.description, '')), 'C')
"""


def _fetch_one(sql, params=None):
    with connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        return cursor.fetchone()


def test_custom_sql_functions_return_expected_values():
    assert _fetch_one("SELECT inmutable_array_to_string(ARRAY['a', NULL, 'b'])") == ("a  b",)
    assert _fetch_one("SELECT provolatile FROM pg_proc WHERE proname = 'inmutable_array_to_string'") == ("i",)
    assert _fetch_one("SELECT array_agg(x ORDER BY x) FROM unnest(array_distinct(ARRAY[2, 1, 2])) x") == ([1, 2],)
    assert _fetch_one(
        "SELECT array_agg(r[1] ORDER BY r[1]) FROM reduce_dim(ARRAY[['b', '2'], ['a', '1']]) r"
    ) == (["a", "b"],)


def test_text_search_index_survives_maintenance():
    project = f.ProjectFactory.create(name="alpha beta", tags=["gamma"])
    f.ProjectFactory.create(name="delta", tags=["epsilon"])
    query = ("SELECT id FROM projects_project "
             "WHERE ({tsvector}) @@ to_tsquery('simple', %s)").format(tsvector=PROJECT_TSVECTOR)

    with connection.cursor() as cursor:
        cursor.execute("REINDEX INDEX projects_project_textquery_idx")
        cursor.execute("ANALYZE projects_project")

        cursor.execute(query, ["alpha"])
        assert cursor.fetchall() == [(project.id,)]
        cursor.execute(query, ["gamma"])
        assert cursor.fetchall() == [(project.id,)]

        cursor.execute("SET LOCAL enable_seqscan = off")
        cursor.execute("EXPLAIN " + query, ["alpha"])
        plan = "\n".join(row[0] for row in cursor.fetchall())
        assert "projects_project_textquery_idx" in plan


@pytest.mark.parametrize("factory_name, bulk_function", [
    ("UserStoryStatusFactory", bulk_order.bulk_update_userstory_status_order),
    ("PointsFactory", bulk_order.bulk_update_points_order),
])
def test_prepared_statement_bulk_order_updates_only_given_project(factory_name, bulk_function):
    factory = getattr(f, factory_name)
    project = f.ProjectFactory.create()
    other_project = f.ProjectFactory.create()
    first = factory.create(project=project, order=1)
    second = factory.create(project=project, order=2)
    untouched = factory.create(project=project, order=3)
    foreign = factory.create(project=other_project, order=4)

    # the foreign id must be ignored because it does not belong to `project`
    bulk_function(project, project.owner, [(first.id, 20), (second.id, 10), (foreign.id, 99)])

    for obj in (first, second, untouched, foreign):
        obj.refresh_from_db()
    assert (first.order, second.order, untouched.order, foreign.order) == (20, 10, 3, 4)


def test_prepared_statement_bulk_order_can_run_twice_in_one_connection():
    # the prepared statement is DEALLOCATEd, so the same name can be prepared again
    project = f.ProjectFactory.create()
    status = f.UserStoryStatusFactory.create(project=project, order=1)

    bulk_order.bulk_update_userstory_status_order(project, project.owner, [(status.id, 5)])
    bulk_order.bulk_update_userstory_status_order(project, project.owner, [(status.id, 6)])

    status.refresh_from_db()
    assert status.order == 6
    assert _fetch_one("SELECT count(*) FROM pg_prepared_statements WHERE name = 'bulk_update_order'") == (0,)


def test_execute_values_bulk_swimlane_order():
    project = f.ProjectFactory.create()
    first = f.SwimlaneFactory.create(project=project, order=1)
    second = f.SwimlaneFactory.create(project=project, order=2)

    bulk_order.bulk_update_swimlane_order(project, project.owner, [(first.id, 7), (second.id, 3)])

    first.refresh_from_db()
    second.refresh_from_db()
    assert (first.order, second.order) == (7, 3)


def test_update_order_and_swimlane_moves_stories_with_execute_values():
    project = f.ProjectFactory.create()
    removed = f.SwimlaneFactory.create(project=project, order=1)
    target = f.SwimlaneFactory.create(project=project, order=2)
    in_removed = f.UserStoryFactory.create(project=project, swimlane=removed, kanban_order=1)
    in_target = f.UserStoryFactory.create(project=project, swimlane=target, kanban_order=1)
    without_swimlane = f.UserStoryFactory.create(project=project, swimlane=None, kanban_order=1)

    bulk_order.update_order_and_swimlane(removed, target)

    for story in (in_removed, in_target, without_swimlane):
        story.refresh_from_db()
    # stories without swimlane first, then target ones, then the ones moved from the removed swimlane
    assert (without_swimlane.swimlane_id, without_swimlane.kanban_order) == (None, 0)
    assert (in_target.swimlane_id, in_target.kanban_order) == (target.id, 1)
    assert (in_removed.swimlane_id, in_removed.kanban_order) == (target.id, 2)


def test_search_service_prefix_query_and_weight_ranking():
    project = f.ProjectFactory.create()
    other_project = f.ProjectFactory.create()
    in_description = f.UserStoryFactory.create(project=project, subject="plain", description="pgeighteen notes")
    in_subject = f.UserStoryFactory.create(project=project, subject="pgeighteen headline", description="")
    f.UserStoryFactory.create(project=project, subject="unrelated", description="nothing")
    f.UserStoryFactory.create(project=other_project, subject="pgeighteen elsewhere")

    # to_tsquery("pgeigh") builds a prefix query: 'pgeigh':*
    results = list(search_services.search_user_stories(project, "pgeigh"))

    # subject weight (A) ranks above description weight (C)
    assert [story.id for story in results] == [in_subject.id, in_description.id]
