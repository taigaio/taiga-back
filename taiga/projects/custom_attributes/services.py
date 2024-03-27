# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import transaction
from django.db import connection


@transaction.atomic
def bulk_update_epic_custom_attribute_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update custom_attributes_epiccustomattribute set "order" = $1
        where custom_attributes_epiccustomattribute.id = $2 and
              custom_attributes_epiccustomattribute.project_id = $3;
    """
    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_userstory_custom_attribute_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update custom_attributes_userstorycustomattribute set "order" = $1
        where custom_attributes_userstorycustomattribute.id = $2 and
              custom_attributes_userstorycustomattribute.project_id = $3;
    """
    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_task_custom_attribute_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update custom_attributes_taskcustomattribute set "order" = $1
        where custom_attributes_taskcustomattribute.id = $2 and
              custom_attributes_taskcustomattribute.project_id = $3;
    """
    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()


@transaction.atomic
def bulk_update_issue_custom_attribute_order(project, user, data):
    cursor = connection.cursor()

    sql = """
    prepare bulk_update_order as update custom_attributes_issuecustomattribute set "order" = $1
        where custom_attributes_issuecustomattribute.id = $2 and
              custom_attributes_issuecustomattribute.project_id = $3;
    """
    cursor.execute(sql)
    for id, order in data:
        cursor.execute("EXECUTE bulk_update_order (%s, %s, %s);",
                       (order, id, project.id))
    cursor.execute("DEALLOCATE bulk_update_order")
    cursor.close()
