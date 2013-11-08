# -*- coding: utf-8 -*-

from contextlib import closing
from django.db import connection


def _get_issues_tags(project):
    extra_sql = ("select unnest(unpickle(tags)) as tagname, count(unnest(unpickle(tags))) "
                 "from issues_issue where project_id = %s "
                 "group by unnest(unpickle(tags)) "
                 "order by tagname asc")

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)

def _get_issues_statuses(project):
    extra_sql = ("select status_id, count(status_id) from issues_issue "
                 "where project_id = %s group by status_id;")

    extra_sql = """
    select id, (select count(*) from issues_issue
                    where project_id = m.project_id and status_id = m.id)
        from projects_issuestatus as m
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_priorities(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and priority_id = m.id)
        from projects_priority as m
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_types(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and type_id = m.id)
        from projects_issuetype as m
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_severities(project):
    extra_sql = """
    select id, (select count(*) from issues_issue
                where project_id = m.project_id and severity_id = m.id)
        from projects_severity as m
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_assigned_to(project):
    extra_sql = """
    select user_id, (select count(*) from issues_issue
                        where project_id = pm.project_id and assigned_to_id = pm.user_id)
        from projects_membership as pm
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_owners(project):
    extra_sql = """
    select user_id, (select count(*) from issues_issue
                        where project_id = pm.project_id and owner_id = pm.user_id)
        from projects_membership as pm
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def _get_issues_created_by(project):
    extra_sql = """
    select user_id, (select count(*) from issues_issue
                        where project_id = pm.project_id and owner_id = pm.user_id)
        from projects_membership as pm
        where project_id = %s;
    """

    with closing(connection.cursor()) as cursor:
        cursor.execute(extra_sql, [project.id])
        rows = cursor.fetchall()

    return dict(rows)


def get_issues_filters_data(project):
    data = {
        "owners": _get_issues_owners(project),
        "tags": _get_issues_tags(project),
        "statuses": _get_issues_statuses(project),
        "priorities": _get_issues_priorities(project),
        "assigned_to": _get_issues_assigned_to(project),
        "created_by": _get_issues_created_by(project),
        "types": _get_issues_types(project),
        "severities": _get_issues_severities(project),
    }
    return data
