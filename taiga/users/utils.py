# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Anler Hernández <hello@anler.me>
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
