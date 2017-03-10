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

from taiga.projects.history.services import get_typename_for_model_class


def attach_total_comments_to_queryset(queryset, as_field="total_comments"):
    """Attach a total comments counter to each object of the queryset.

    :param queryset: A Django projects queryset object.
    :param as_field: Attach the counter as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    sql = """
             SELECT COUNT(history_historyentry.id)
               FROM history_historyentry
              WHERE history_historyentry.key = CONCAT('{key_prefix}', {tbl}.id) AND
                    history_historyentry.comment is not null AND
                    history_historyentry.comment != ''
          """

    typename = get_typename_for_model_class(model)

    sql = sql.format(tbl=model._meta.db_table, key_prefix="{}:".format(typename))

    queryset = queryset.extra(select={as_field: sql})
    return queryset
