# -*- coding: utf-8 -*-
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


def apply_order_updates(base_orders: dict, new_orders: dict):
    """
    `base_orders` must be a dict containing all the elements that can be affected by
    order modifications.
    `new_orders` must be a dict containing the basic order modifications to apply.

    The result will a base_orders with the specified order changes in new_orders
    and the extra calculated ones applied.
    Extra order updates can be needed when moving elements to intermediate positions.
    The elements where no order update is needed will be removed.
    """
    updated_order_ids = set()
    # We will apply the multiple order changes by the new position order
    sorted_new_orders = [(k, v) for k, v in new_orders.items()]
    sorted_new_orders = sorted(sorted_new_orders, key=lambda e: e[1])

    for new_order in sorted_new_orders:
        old_order = base_orders[new_order[0]]
        new_order = new_order[1]
        for id, order in base_orders.items():
            # When moving forward only the elements contained in the range new_order - old_order
            # positions need to be updated
            moving_backward = new_order <= old_order and order >= new_order and order < old_order
            # When moving backward all the elements from the new_order position need to bee updated
            moving_forward = new_order >= old_order and order >= new_order
            if moving_backward or moving_forward:
                base_orders[id] += 1
                updated_order_ids.add(id)

    # Overwritting the orders specified
    for id, order in new_orders.items():
        if base_orders[id] != order:
            base_orders[id] = order
            updated_order_ids.add(id)

    # Remove not modified elements
    removing_keys = [id for id in base_orders if id not in updated_order_ids]
    [base_orders.pop(id, None) for id in removing_keys]


def update_projects_order_in_bulk(bulk_data: list, field: str, user):
    """
    Update the order of user projects in the user membership.
    `bulk_data` should be a list of dicts with the following format:

    [{'project_id': <value>, 'order': <value>}, ...]
    """
    memberships_orders = {m.id: getattr(m, field) for m in user.memberships.all()}
    new_memberships_orders = {}

    for membership_data in bulk_data:
        project_id = membership_data["project_id"]
        with suppress(ObjectDoesNotExist):
            membership = user.memberships.get(project_id=project_id)
            new_memberships_orders[membership.id] = membership_data["order"]

    apply_order_updates(memberships_orders, new_memberships_orders)

    from taiga.base.utils import db
    db.update_attr_in_bulk_for_ids(memberships_orders, field, model=models.Membership)


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
