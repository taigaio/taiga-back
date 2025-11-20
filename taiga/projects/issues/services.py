# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import io
import csv
import json
import logging
from collections import OrderedDict
from operator import itemgetter
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db import connection
from django.utils.translation import gettext as _

from taiga.base.utils import db, text
from taiga.events import events
from taiga.doubai_ai import ask_once # Import ask_once function

from taiga.projects.history.services import take_snapshot
from taiga.projects.issues.apps import connect_issues_signals, disconnect_issues_signals
from taiga.projects.votes.utils import attach_total_voters_to_queryset
from taiga.projects.notifications.utils import attach_watchers_to_queryset

from . import models

logger = logging.getLogger(__name__)


#####################################################
# Bulk actions
#####################################################


def get_issues_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of issues.

    :param bulk_data: List of issues in bulk format.
    :param additional_fields: Additional fields when instantiating each issue.

    :return: List of `Issue` instances.
    """
    return [
        models.Issue(subject=line, **additional_fields)
        for line in text.split_in_lines(bulk_data)
    ]


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
            issue = models.Issue.objects.get(pk=issue_data["issue_id"])
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

    events.emit_event_for_ids(
        ids=issue_ids, content_type="issues.issues", projectid=milestone.project.pk
    )

    db.update_attr_in_bulk_for_ids(issue_milestones, "milestone_id", model=models.Issue)

    return issue_milestones


#####################################################
# CSV
#####################################################


def issues_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = [
        "id",
        "ref",
        "subject",
        "description",
        "sprint_id",
        "sprint",
        "sprint_estimated_start",
        "sprint_estimated_finish",
        "owner",
        "owner_full_name",
        "assigned_to",
        "assigned_to_full_name",
        "status",
        "severity",
        "priority",
        "type",
        "is_closed",
        "attachments",
        "external_reference",
        "tags",
        "watchers",
        "voters",
        "created_date",
        "modified_date",
        "finished_date",
        "due_date",
        "due_date_reason",
    ]

    custom_attrs = project.issuecustomattributes.all()
    for custom_attr in custom_attrs:
        fieldnames.append(custom_attr.name)

    queryset = queryset.prefetch_related(
        "attachments", "generated_user_stories", "custom_attributes_values"
    )
    queryset = queryset.select_related("owner", "assigned_to", "status", "project")
    queryset = attach_total_voters_to_queryset(queryset)
    queryset = attach_watchers_to_queryset(queryset)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for issue in queryset:
        issue_data = {
            "id": issue.id,
            "ref": issue.ref,
            "subject": text.sanitize_csv_text_value(issue.subject),
            "description": text.sanitize_csv_text_value(issue.description),
            "sprint_id": issue.milestone.id if issue.milestone else None,
            "sprint": (
                text.sanitize_csv_text_value(issue.milestone.name)
                if issue.milestone
                else None
            ),
            "sprint_estimated_start": (
                issue.milestone.estimated_start if issue.milestone else None
            ),
            "sprint_estimated_finish": (
                issue.milestone.estimated_finish if issue.milestone else None
            ),
            "owner": issue.owner.username if issue.owner else None,
            "owner_full_name": (
                text.sanitize_csv_text_value(issue.owner.get_full_name())
                if issue.owner
                else None
            ),
            "assigned_to": issue.assigned_to.username if issue.assigned_to else None,
            "assigned_to_full_name": (
                text.sanitize_csv_text_value(issue.assigned_to.get_full_name())
                if issue.assigned_to
                else None
            ),
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
            value = issue.custom_attributes_values.attributes_values.get(
                str(custom_attr.id), None
            )
            issue_data[custom_attr.name] = text.sanitize_csv_text_value(value)

        writer.writerow(issue_data)

    return csv_data


#####################################################
# Api filter data
#####################################################


def _get_issues_statuses(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": color,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_issues_types(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": color,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_issues_priorities(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": color,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_issues_severities(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, color, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": color,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_issues_assigned_to(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id] + where_params)
        rows = cursor.fetchall()

    result = []
    none_valued_added = False
    for id, full_name, username, count in rows:
        result.append(
            {
                "id": id,
                "full_name": full_name or username or "",
                "count": count,
            }
        )

        if id is None:
            none_valued_added = True

    # If there was no issue with null assigned_to we manually add it
    if not none_valued_added:
        result.append(
            {
                "id": None,
                "full_name": "",
                "count": 0,
            }
        )

    return sorted(result, key=itemgetter("full_name"))


def _get_issues_owners(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, username, count in rows:
        if count > 0:
            result.append(
                {
                    "id": id,
                    "full_name": full_name or username or "",
                    "count": count,
                }
            )
    return sorted(result, key=itemgetter("full_name"))


def _get_issues_roles(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, name, order, count in rows:
        result.append(
            {
                "id": id,
                "name": _(name),
                "color": None,
                "order": order,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("order"))


def _get_issues_tags(project, queryset):
    compiler = connection.ops.compiler(queryset.query.compiler)(
        queryset.query, connection, None
    )
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
    """.format(
        where=where
    )

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for name, color, count in rows:
        result.append(
            {
                "name": name,
                "color": color,
                "count": count,
            }
        )
    return sorted(result, key=itemgetter("name"))


def get_issues_filters_data(project, querysets):
    """
    Given a project and an issues queryset, return a simple data structure
    of all possible filters for the issues in the queryset.
    """
    data = OrderedDict(
        [
            ("types", _get_issues_types(project, querysets["types"])),
            ("statuses", _get_issues_statuses(project, querysets["statuses"])),
            ("priorities", _get_issues_priorities(project, querysets["priorities"])),
            ("severities", _get_issues_severities(project, querysets["severities"])),
            ("assigned_to", _get_issues_assigned_to(project, querysets["assigned_to"])),
            ("owners", _get_issues_owners(project, querysets["owners"])),
            ("tags", _get_issues_tags(project, querysets["tags"])),
            ("roles", _get_issues_roles(project, querysets["roles"])),
        ]
    )

    return data


#####################################################
# AI services
#####################################################


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


def analyze_issues_with_ai(issues, max_workers=10):
    """
    Analyzes a batch of issues in parallel using an AI model.

    Args:
        issues (list): A list of issue data dictionaries.
        max_workers (int): The maximum number of threads to use.

    Returns:
        list: A list of analysis results for each issue.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_issue = {executor.submit(_analyze_single_issue, issue): issue for issue in issues}

        for future in as_completed(future_to_issue):
            issue = future_to_issue[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze issue {issue.get('id')}: {e}")
                results.append({
                    "issue_id": issue.get("id"),
                    "issue_ref": issue.get("ref"),
                    "subject": issue.get("subject"),
                    "analysis": _get_default_analysis(),
                    "error": str(e)
                })

    results.sort(key=lambda x: (x["issue_id"] is None, x["issue_id"]))
    return results


def _analyze_single_issue(issue):
    """
    Analyzes a single issue using the Doubao AI API.
    """
    try:
        # 1. Build Prompt and Question
        system_prompt = "You are a project management expert, skilled in analyzing software development issues. Your response must be a valid JSON object."
        question = _build_analysis_prompt(issue)
        
        # 2. Call ask_once function
        ai_text_response = ask_once(question=question, prompt=system_prompt)
        
        # 3. Parse the returned text
        analysis = _parse_ai_response(ai_text_response)

        return {
            "issue_id": issue.get("id"),
            "issue_ref": issue.get("ref"),
            "subject": issue.get("subject"),
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Doubao AI analysis failed for issue {issue.get('id')}: {e}")
        raise AIServiceError(str(e))


def _build_analysis_prompt(issue):
    """Builds the prompt for the AI model based on issue data."""
    return f"""You are a project management expert, skilled in analyzing software development Issues.

Please analyze the following Issue:
- ID: {issue.get('id')}
- Title: {issue.get('subject')}
- Description: {issue.get('description', 'N/A')}
- Current Type: {issue.get('type')}
- Current Priority: {issue.get('priority')}
- Current Severity: {issue.get('severity')}
- Tags: {issue.get('tags', '[]')}

Please provide the following analysis result in a valid JSON format:
1.  `priority`: Recommended priority (Low/Normal/High).
2.  `priority_reason`: Reason for the priority recommendation (1 sentence).
3.  `type`: Recommended type (Bug/Question/Enhancement).
4.  `severity`: Recommended severity (Wishlist/Minor/Normal/Important/Critical).
5.  `description`: A brief analysis of the problem (2-3 sentences).
6.  `related_modules`: A list of 2-4 potentially related software modules.
7.  `solutions`: A list of 3-5 suggested solutions or next steps.
8.  `confidence`: Your confidence score for this analysis (from 0.0 to 1.0).

IMPORTANT:
- Your entire response MUST be a single, valid JSON object.
- Do not include any text or formatting outside of the JSON object.
- Ensure all fields in the JSON object have a value.
- The `related_modules` array should contain 2 to 4 items.
- The `solutions` array should contain 3 to 5 items.
- All text values in the JSON should be in English."""


def _parse_ai_response(ai_text):
    """Parses the JSON response from the AI, handling potential markdown code blocks."""
    try:
        json_start = ai_text.find('{')
        json_end = ai_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in AI response")
        json_str = ai_text[json_start:json_end]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse AI response: {e}\nRaw: {ai_text}")
        return _get_default_analysis()


def _get_default_analysis():
    """Returns a default analysis object for fallback cases."""
    return {
        "priority": "Normal",
        "priority_reason": "AI analysis failed, using default value.",
        "type": "Question",
        "severity": "Normal",
        "description": "AI service is temporarily unavailable. Please try again later or analyze manually.",
        "related_modules": ["Unknown Module"],
        "solutions": ["Please check the issue details manually."],
        "confidence": 0.0
    }
