# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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

from collections import namedtuple

from django.db import connection

Neighbor = namedtuple("Neighbor", "left right")


def get_neighbors(obj, results_set=None):
    """Get the neighbors of a model instance.

    The neighbors are the objects that are at the left/right of `obj` in the results set.

    :param obj: The object you want to know its neighbors.
    :param results_set: Find the neighbors applying the constraints of this set (a Django queryset
        object).

    :return: Tuple `<left neighbor>, <right neighbor>`. Left and right neighbors can be `None`.
    """
    if results_set is None or results_set.count() == 0:
        results_set = type(obj).objects.get_queryset()

    compiler = results_set.query.get_compiler('default')
    base_sql, base_params = compiler.as_sql(with_col_aliases=True)

    query = """
        SELECT * FROM
            (SELECT "id" as id, ROW_NUMBER() OVER()
                FROM (%s) as ID_AND_ROW)
        AS SELECTED_ID_AND_ROW
        """ % (base_sql)
    query += " WHERE id=%s;"
    params = list(base_params) + [obj.id]

    cursor = connection.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row is None:
        return Neighbor(None, None)

    obj_position = row[1] - 1

    try:
        left = obj_position > 0 and results_set[obj_position - 1] or None
    except IndexError:
        left = None

    try:
        right = results_set[obj_position + 1]
    except IndexError:
        right = None

    return Neighbor(left, right)
