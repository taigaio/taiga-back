# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import csv
from collections import OrderedDict
from operator import itemgetter
from contextlib import closing

from django.db import connection
from django.utils.translation import ugettext as _

from taiga.base.utils import db, text
from taiga.projects.issues.apps import (
    connect_issues_signals,
    disconnect_issues_signals)
from taiga.projects.votes import services as votes_services
from . import models


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


def update_issues_order_in_bulk(bulk_data):
    """Update the order of some issues.

    `bulk_data` should be a list of tuples with the following format:

    [(<issue id>, <new issue order value>), ...]
    """
    issue_ids = []
    new_order_values = []
    for issue_id, new_order_value in bulk_data:
        issue_ids.append(issue_id)
        new_order_values.append({"order": new_order_value})
    db.update_in_bulk_with_ids(issue_ids, new_order_values, model=models.Issue)


def issues_to_csv(project, queryset):
    csv_data = io.StringIO()
    fieldnames = ["ref", "subject", "description", "milestone", "owner",
                  "owner_full_name", "assigned_to", "assigned_to_full_name",
                  "status", "severity", "priority", "type", "is_closed",
                  "attachments", "external_reference", "tags",
                  "watchers", "voters",
                  "created_date", "modified_date", "finished_date"]
    for custom_attr in project.issuecustomattributes.all():
        fieldnames.append(custom_attr.name)

    writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
    writer.writeheader()
    for issue in queryset:
        issue_data = {
            "ref": issue.ref,
            "subject": issue.subject,
            "description": issue.description,
            "milestone": issue.milestone.name if issue.milestone else None,
            "owner": issue.owner.username if issue.owner else None,
            "owner_full_name": issue.owner.get_full_name() if issue.owner else None,
            "assigned_to": issue.assigned_to.username if issue.assigned_to else None,
            "assigned_to_full_name": issue.assigned_to.get_full_name() if issue.assigned_to else None,
            "status": issue.status.name,
            "severity": issue.severity.name,
            "priority": issue.priority.name,
            "type": issue.type.name,
            "is_closed": issue.is_closed,
            "attachments": issue.attachments.count(),
            "external_reference": issue.external_reference,
            "tags": ",".join(issue.tags or []),
            "watchers": [u.id for u in issue.get_watchers()],
            "voters": votes_services.get_voters(issue).count(),
            "created_date": issue.created_date,
            "modified_date": issue.modified_date,
            "finished_date": issue.finished_date,
        }

        for custom_attr in project.issuecustomattributes.all():
            value = issue.custom_attributes_values.attributes_values.get(str(custom_attr.id), None)
            issue_data[custom_attr.name] = value

        writer.writerow(issue_data)

    return csv_data


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
        SELECT
        	"projects_membership"."user_id" user_id,
        	"users_user"."full_name",
        	COALESCE("counters".count, 0) count
        FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."assigned_to_id")
        INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
        WHERE "projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL

        -- unassigned issues
        UNION
        SELECT NULL user_id, NULL,  count(coalesce(assigned_to_id, -1)) count
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
    for id, full_name, count in rows:
        result.append({
            "id": id,
            "full_name": full_name or "",
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
        SELECT
        	"projects_membership"."user_id" id,
        	"users_user"."full_name",
        	COALESCE("counters".count, 0) count
        FROM projects_membership
        LEFT OUTER JOIN counters ON ("projects_membership"."user_id" = "counters"."owner_id")
        INNER JOIN "users_user" ON ("projects_membership"."user_id" = "users_user"."id")
        WHERE ("projects_membership"."project_id" = %s AND "projects_membership"."user_id" IS NOT NULL)

        -- System users
        UNION
    		SELECT
    			"users_user"."id" user_id,
    			"users_user"."full_name" full_name,
    			COALESCE("counters".count, 0) count
    		FROM users_user
    		LEFT OUTER JOIN counters ON ("users_user"."id" = "counters"."owner_id")
    		WHERE ("users_user"."is_system" IS TRUE)
    """.format(where=where)

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, where_params + [project.id])
        rows = cursor.fetchall()

    result = []
    for id, full_name, count in rows:
        if count > 0:
            result.append({
                "id": id,
                "full_name": full_name,
                "count": count,
            })
    return sorted(result, key=itemgetter("full_name"))


def _get_issues_tags(queryset):
    tags = []
    for t_list in queryset.values_list("tags", flat=True):
        if t_list is None:
            continue
        tags += list(t_list)

    tags = [{"name":e, "count":tags.count(e)} for e in set(tags)]

    return sorted(tags, key=itemgetter("name"))


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
        ("tags", _get_issues_tags(querysets["tags"])),
    ])

    return data
