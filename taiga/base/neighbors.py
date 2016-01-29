# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.sql.datastructures import EmptyResultSet
from taiga.base.api import serializers

Neighbor = namedtuple("Neighbor", "left right")


def get_neighbors(obj, results_set=None):
    """Get the neighbors of a model instance.

    The neighbors are the objects that are at the left/right of `obj` in the results set.

    :param obj: The object you want to know its neighbors.
    :param results_set: Find the neighbors applying the constraints of this set (a Django queryset
        object).

    :return: Tuple `<left neighbor>, <right neighbor>`. Left and right neighbors can be `None`.
    """
    if results_set is None:
        results_set = type(obj).objects.get_queryset()

    # Neighbors calculation is at least at project level
    results_set = results_set.filter(project_id=obj.project.id)

    compiler = results_set.query.get_compiler('default')
    try:
        base_sql, base_params = compiler.as_sql(with_col_aliases=True)
    except EmptyResultSet:
        # Generate a not empty queryset
        results_set = type(obj).objects.get_queryset().filter(project_id=obj.project.id)
        compiler = results_set.query.get_compiler('default')
        base_sql, base_params = compiler.as_sql(with_col_aliases=True)

    query = """
        SELECT * FROM
            (SELECT "col1" as id,
                    ROW_NUMBER() OVER(),
                    LAG("col1", 1) OVER() AS prev,
                    LEAD("col1", 1) OVER() AS next
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
    left_object_id = row[2]
    right_object_id = row[3]

    try:
        left = results_set.get(id=left_object_id)
    except ObjectDoesNotExist:
        left = None

    try:
        right = results_set.get(id=right_object_id)
    except ObjectDoesNotExist:
        right = None

    return Neighbor(left, right)


class NeighborsSerializerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["neighbors"] = serializers.SerializerMethodField("get_neighbors")

    def serialize_neighbor(self, neighbor):
        raise NotImplementedError

    def get_neighbors(self, obj):
        view, request = self.context.get("view", None), self.context.get("request", None)
        if view and request:
            queryset = view.filter_queryset(view.get_queryset())
            left, right = get_neighbors(obj, results_set=queryset)
        else:
            left = right = None

        return {
            "previous": self.serialize_neighbor(left),
            "next": self.serialize_neighbor(right)
        }
