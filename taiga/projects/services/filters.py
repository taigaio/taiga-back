# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from contextlib import closing
from django.db import connection


def _get_stories_tags(project):
    result = set()
    for tags in project.user_stories.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


def _get_tasks_tags(project):
    result = set()
    for tags in project.tasks.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


def _get_issues_tags(project):
    result = set()
    for tags in project.issues.values_list("tags", flat=True):
        if tags:
            result.update(tags)
    return result


def _get_issues_tags_with_count(project):
    extra_sql = ("select unnest(tags) as tagname, count(unnest(tags)) "
                 "from issues_issue where project_id = %s "
                 "group by unnest(tags) "
                 "order by tagname asc")

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows


def _get_issues_statuses(project):
    extra_sql = ("select status_id, count(status_id) from issues_issue "
                 "where project_id = %s group by status_id;")

    extra_sql = """
    select id, (select count(*) from issues_issue
                    where project_id = m.project_id and status_id = m.id)
        from projects_issuestatus as m
        where project_id = %s order by m.order;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows


def _get_issues_priorities(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and priority_id = m.id)
        from projects_priority as m
        where project_id = %s order by m.order;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows

def _get_issues_types(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and type_id = m.id)
        from projects_issuetype as m
        where project_id = %s order by m.order;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows


def _get_issues_severities(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and severity_id = m.id)
        from projects_severity as m
        where project_id = %s order by m.order;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows


def _get_issues_assigned_to(project):
    extra_sql = """
    select null, (select count(*) from issues_issue
                        where project_id = %s and assigned_to_id is null)
    UNION select user_id, (select count(*) from issues_issue
                        where project_id = pm.project_id and assigned_to_id = pm.user_id)
        from projects_membership as pm
        where project_id = %s and pm.user_id is not null;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id, project.id])
        rows = cursor.fetchall()

    return rows


def _get_issues_owners(project):
    extra_sql = """
    select user_id, (select count(*) from issues_issue
                        where project_id = pm.project_id and owner_id = pm.user_id)
        from projects_membership as pm
        where project_id = %s and pm.user_id is not null;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return rows


# Public api

def get_all_tags(project):
    """
    Given a project, return sorted list of unique
    tags found on it.
    """
    result = set()
    result.update(_get_issues_tags(project))
    result.update(_get_stories_tags(project))
    result.update(_get_tasks_tags(project))
    return sorted(result)


def get_issues_filters_data(project):
    """
    Given a project, return a simple data structure
    of all possible filters for issues.
    """

    data = {
        "types": _get_issues_types(project),
        "statuses": _get_issues_statuses(project),
        "priorities": _get_issues_priorities(project),
        "severities": _get_issues_severities(project),
        "assigned_to": _get_issues_assigned_to(project),
        "owners": _get_issues_owners(project),
        "tags": _get_issues_tags_with_count(project),
    }

    return data
