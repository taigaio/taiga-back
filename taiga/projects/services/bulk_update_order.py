# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.db import transaction, connection
from django.core.exceptions import ObjectDoesNotExist

from taiga.projects import models

from contextlib import suppress


def update_projects_order_in_bulk(bulk_data:list, field:str, user):
    """
    Update the order of user projects in the user membership.
    `bulk_data` should be a list of tuples with the following format:

    [(<project id>, {<field>: <value>, ...}), ...]
    """
    membership_ids = []
    new_order_values = []
    for membership_data in bulk_data:
        project_id = membership_data["project_id"]
        with suppress(ObjectDoesNotExist):
            membership = user.memberships.get(project_id=project_id)
            membership_ids.append(membership.id)
            new_order_values.append({field: membership_data["order"]})

    from taiga.base.utils import db

    db.update_in_bulk_with_ids(membership_ids, new_order_values, model=models.Membership)


@transaction.atomic
def bulk_update_userstory_status_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_userstorystatus set "order" = $1
        where projects_userstorystatus.id = $2 and
              projects_userstorystatus.project_id = $3;
    """
    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_points_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_points set "order" = $1
        where projects_points.id = $2 and
              projects_points.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_task_status_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_taskstatus set "order" = $1
        where projects_taskstatus.id = $2 and
              projects_taskstatus.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_issue_status_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_issuestatus set "order" = $1
        where projects_issuestatus.id = $2 and
              projects_issuestatus.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_issue_type_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_issuetype set "order" = $1
        where projects_issuetype.id = $2 and
              projects_issuetype.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_priority_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_priority set "order" = $1
        where projects_priority.id = $2 and
              projects_priority.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_severity_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update projects_severity set "order" = $1
        where projects_severity.id = $2 and
              projects_severity.project_id = $3;
    """

    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()
