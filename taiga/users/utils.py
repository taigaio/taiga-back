# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

def attach_roles(queryset, as_field="roles_attr"):
    """Attach roles to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the roles as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """SELECT ARRAY(
                    SELECT DISTINCT(users_role.name)
                      FROM projects_membership
                INNER JOIN users_role ON users_role.id = projects_membership.role_id
                     WHERE projects_membership.user_id = {tbl}.id
                  ORDER BY users_role.name)
    """
    sql = sql.format(tbl=model._meta.db_table)
    queryset = queryset.extra(select={as_field: sql})
    return queryset


def attach_extra_info(queryset, user=None):
    queryset = attach_roles(queryset)
    return queryset
