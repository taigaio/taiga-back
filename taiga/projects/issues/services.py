# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import io
import csv
from collections import OrderedDict
from operator import itemgetter
from contextlib import closing

from django.db import connection
from django.utils.translation import gettext as _

from taiga.base.utils import db, text
from taiga.events import events

from taiga.projects.history.services import take_snapshot
from taiga.projects.issues.apps import (
    connect_issues_signals,
    disconnect_issues_signals)
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset

from . import models


#####################################################
# Bulk actions
#####################################################

def get_issues_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of issues.

    :param bulk_data: List of issues in bulk format.
    :param additional_fields: Additional fields when instantiating each issue.

    :return: List of `Issue` instances.
    """
    return [models.Issue(subject=line, **additional_fields)
            for line in text.split_in_lines(bulk_data)]


def create_issues_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create issues from `bulk_data`.

    :param bulk_data: List of issues in bulk format.
    :param callback: Callback to execute after each issue save.
    :param additional_fields: Additional fields when instantiating each issue.

    :return: List of created `Issue` instances.
    """
    issues = get_issues_from_bulk(bulk_data, **additional_fields)

    disconnect_issues_signals()

    try:
        db.save_in_bulk(issues, callback, precall)
    finally:
        connect_issues_signals()

    return issues


def snapshot_issues_in_bulk(bulk_data, user):
    for issue_data in bulk_data:
        try:
            issue = models.Issue.objects.get(pk=issue_data['issue_id'])
            take_snapshot(issue, user=user)
        except models.Issue.DoesNotExist:
            pass


def update_issues_milestone_in_bulk(bulk_data: list, milestone: object):
    """
    Update the milestone some issues adding
    `bulk_data` should be a list of dicts with the following format:
    [{'task_id': <value>}, ...]
    """
    issue_milestones = {e["issue_id"]: milestone.id for e in bulk_data}
    issue_ids = issue_milestones.keys()

    events.emit_event_for_ids(ids=issue_ids,
                              content_type="issues.issues",
                              projectid=milestone.project.pk)

    db.update_attr_in_bulk_for_ids(issue_milestones, "milestone_id",
                                   model=models.Issue)

    return issue_milestones

#####################################################
# CSV
#####################################################


def issues_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["id", "ref", "subject", "description", "sprint_id", "sprint",
                  "sprint_estimated_start", "sprint_estimated_finish", "owner",
                  "owner_full_name", "assigned_to", "assigned_to_full_name",
                  "status", "severity", "priority", "type", "is_closed",
                  "attachments", "external_reference", "tags",  "watchers",
                  "voters", "created_date", "modified_date", "finished_date",
                  "due_date", "due_date_reason"]

    custom_attrs = project.issuecustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related("attachments",
                                         "generated_user_stories",
                                         "custom_attributes_values")
    queryset = queryset.select_related("owner",
                                       "assigned_to",
                                       "status",
                                       "project")
    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for issue in queryset:
        issue_data = {
            "id": issue.id,
            "ref": issue.ref,
            "subject": issue.subject,
            "description": issue.description,
            "sprint_id": issue.milestone.id if issue.milestone else None,
            "sprint": issue.milestone.name if issue.milestone else None,
            "sprint_estimated_start": issue.milestone.estimated_start if issue.milestone else None,
            "sprint_estimated_finish": issue.milestone.estimated_finish if issue.milestone else None,
            "owner": issue.owner.username if issue.owner else None,
            "owner_full_name": issue.owner.get_full_name() if issue.owner else None,
            "assigned_to": issue.assigned_to.username if issue.assigned_to else None,
            "assigned_to_full_name": issue.assigned_to.get_full_name() if issue.assigned_to else None,
            "status": issue.status.name if issue.status else None,
            "severity": issue.severity.name,
            "priority": issue.priority.name,
            "type": issue.type.name,
            "is_closed": issue.is_closed,
            "attachments": issue.attachments.count(),
            "external_reference": issue.external_reference,
            "tags": ",".join(issue.tags or []),
            "watchers": issue.watchers,
            "voters": issue.total_voters,
            "created_date": issue.created_date,
            "modified_date": issue.modified_date,
            "finished_date": issue.finished_date,
            "due_date": issue.due_date,
            "due_date_reason": issue.due_date_reason,
        }

        for custom_attr in custom_attrs:
            if not hasattr(issue, "custom_attributes_values"):
                continue
            value = issue.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            issue_data[custom_attr.name] = value

        writer.writerow(issue_data)

    return csv_data


#####################################################
# Api filter data
#####################################################

def _get_issues_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT status_id, count(status_id) count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY status_id
        )

                 SELECT "projects_issuestatus"."id",
                        "projects_issuestatus"."name",
                        "projects_issuestatus"."color",
                        "projects_issuestatus"."order",
                        COALESCE(counters.count, 0)
                   FROM "projects_issuestatus"
        LEFT OUTER JOIN counters ON counters.status_id = projects_issuestatus.id
                  WHERE "projects_issuestatus"."project_id" = %s
               ORDER BY "projects_issuestatus"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": color,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def _get_issues_types(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT type_id, count(type_id) count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY type_id
        )

                 SELECT "projects_issuetype"."id",
                        "projects_issuetype"."name",
                        "projects_issuetype"."color",
                        "projects_issuetype"."order",
                        COALESCE(counters.count, 0)
                   FROM "projects_issuetype"
        LEFT OUTER JOIN counters ON counters.type_id = projects_issuetype.id
                  WHERE "projects_issuetype"."project_id" = %s
               ORDER BY "projects_issuetype"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": color,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def _get_issues_priorities(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT priority_id, count(priority_id) count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY priority_id
        )

                 SELECT "projects_priority"."id",
                        "projects_priority"."name",
                        "projects_priority"."color",
                        "projects_priority"."order",
                        COALESCE(counters.count, 0)
                   FROM "projects_priority"
        LEFT OUTER JOIN counters ON counters.priority_id = projects_priority.id
                  WHERE "projects_priority"."project_id" = %s
               ORDER BY "projects_priority"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": color,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def _get_issues_severities(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT severity_id, count(severity_id) count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY severity_id
        )

                 SELECT "projects_severity"."id",
                        "projects_severity"."name",
                        "projects_severity"."color",
                        "projects_severity"."order",
                        COALESCE(counters.count, 0)
                   FROM "projects_severity"
        LEFT OUTER JOIN counters ON counters.severity_id = projects_severity.id
                  WHERE "projects_severity"."project_id" = %s
               ORDER BY "projects_severity"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": color,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))


def _get_issues_assigned_to(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT assigned_to_id,  count(assigned_to_id) count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where} AND "issues_issue"."assigned_to_id" IS NOT NULL
              GROUP BY assigned_to_id
        )

                SELECT  "projects_membership"."user_id" user_id,
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."assigned_to_id")
             INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- unassigned issues
        UNION

                 SELECT NULL user_id, NULL, NULL, count(coalesce(assigned_to_id, -1)) count
                   FROM "issues_issue"
             INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                  WHERE {where} AND "issues_issue"."assigned_to_id" IS NULL
               GROUP BY assigned_to_id
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count in rows:
        result.append({
            "id": id,
            "full_name": full_name or username or "",
            "count": count,
        })

        if id is None:
            none_valued_added = True

    # If there was no issue with null assigned_to we manually add it
    if not none_valued_added:
        result.append({
            "id": None,
            "full_name": "",
            "count": 0,
        })

    return sorted(result, key=itemgetter("full_name"))


def _get_issues_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH counters AS (
                SELECT "issues_issue"."owner_id" owner_id,  count("issues_issue"."owner_id") count
                  FROM "issues_issue"
            INNER JOIN "projects_project" ON ("issues_issue"."project_id" = "projects_project"."id")
                 WHERE {where}
              GROUP BY "issues_issue"."owner_id"
        )

                 SELECT "projects_membership"."user_id" id,
                        "users_user"."full_name",
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."owner_id")
             INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
                  WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- System users
        UNION

                 SELECT "users_user"."id" user_id,
                        "users_user"."full_name" full_name,
                        "users_user"."username",
                        COALESCE("counters".count, 0) count
                   FROM users_user
        LEFT OUTER JOIN counters ON ("users_user"."id" = "counters"."owner_id")
                  WHERE ("users_user"."is_system" IS TRUE)
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, username, count in rows:
        if count > 0:
            result.append({
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
            })
    return sorted(result, key=itemgetter("full_name"))


def _get_issues_roles(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
     WITH "issue_counters" AS (
         SELECT DISTINCT "issues_issue"."status_id" "status_id",
                         "issues_issue"."id" "issue_id",
                         "projects_membership"."role_id" "role_id"
                    FROM "issues_issue"
              INNER JOIN "projects_project"
                      ON ("issues_issue"."project_id" = "projects_project"."id")
         LEFT OUTER JOIN "projects_membership"
                      ON "projects_membership"."user_id" = "issues_issue"."assigned_to_id"
                   WHERE {where}
            ),
             "counters" AS (
                  SELECT "role_id" as "role_id",
                         COUNT("role_id") "count"
                    FROM "issue_counters"
                GROUP BY "role_id"
            )

                 SELECT "users_role"."id",
                        "users_role"."name",
                        "users_role"."order",
                        COALESCE("counters"."count", 0)
                   FROM "users_role"
        LEFT OUTER JOIN "counters"
                     ON "counters"."role_id" = "users_role"."id"
                  WHERE "users_role"."project_id" = %s
               ORDER BY "users_role"."order";
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, order, count in rows:
        result.append({
            "id": id,
            "name": _(name),
            "color": None,
            "order": order,
            "count": count,
        })
    return sorted(result, key=itemgetter("order"))

def _get_issues_tags(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(queryset.query, connection, None)
    queryset_where_tuple = queryset.query.where.as_sql(compiler, connection)
    where = queryset_where_tuple[0]
    where_params = queryset_where_tuple[1]

    extra_sql = """
        WITH "issues_tags" AS (
                    SELECT "tag",
                           COUNT("tag") "counter"
                      FROM (
                                SELECT UNNEST("issues_issue"."tags") "tag"
                                  FROM "issues_issue"
                            INNER JOIN "projects_project"
                                    ON ("issues_issue"."project_id" = "projects_project"."id")
                                 WHERE {where}
                           ) "tags"
                  GROUP BY "tag"),
             "project_tags" AS (
                    SELECT reduce_dim("tags_colors") "tag_color"
                      FROM "projects_project"
                     WHERE "id"=%s)

      SELECT "tag_color"[1] "tag",
             "tag_color"[2] "color",
             COALESCE("issues_tags"."counter", 0) "counter"
        FROM project_tags
   LEFT JOIN "issues_tags" ON "project_tags"."tag_color"[1] = "issues_tags"."tag"
    ORDER BY "tag"
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for name, color, count in rows:
        result.append({
            "name": name,
            "color": color,
            "count": count,
        })
    return sorted(result, key=itemgetter("name"))


def get_issues_filters_data(project, querysets):
    """
    Given a project and an issues queryset, return a simple data structure
    of all possible filters for the issues in the queryset.
    """
    data = OrderedDict([
        ("types", _get_issues_types(project, querysets["types"])),
        ("statuses", _get_issues_statuses(project, querysets["statuses"])),
        ("priorities", _get_issues_priorities(project, querysets["priorities"])),
        ("severities", _get_issues_severities(project, querysets["severities"])),
        ("assigned_to", _get_issues_assigned_to(project, querysets["assigned_to"])),
        ("owners", _get_issues_owners(project, querysets["owners"])),
        ("tags", _get_issues_tags(project, querysets["tags"])),
        ("roles", _get_issues_roles(project, querysets["roles"])),
    ])

    return data
