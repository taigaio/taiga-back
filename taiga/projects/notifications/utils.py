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

from django.apps import apps
from .choices import NotifyLevel
from taiga.base.utils.text import strip_lines

def attach_watchers_to_queryset(queryset, as_field="watchers"):
    """Attach watching user ids to each object of the queryset.

    :param queryset: A Django queryset object.
    :param as_field: Attach the watchers as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)

    sql = ("""SELECT array(SELECT user_id
                           FROM notifications_watched
                           WHERE notifications_watched.content_type_id = {type_id}
                           AND notifications_watched.object_id = {tbl}.id)""")
    sql = sql.format(type_id=type.id, tbl=model._meta.db_table)
    qs = queryset.extra(select={as_field: sql})

    return qs


def attach_is_watcher_to_queryset(queryset, user, as_field="is_watcher"):
    """Attach is_watcher boolean to each object of the queryset.

    :param queryset: A Django queryset object.
    :param user: A users.User object model
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    if user is None or user.is_anonymous:
        sql = """SELECT false"""
    else:
        sql = ("""SELECT CASE WHEN (SELECT count(*)
                                      FROM notifications_watched
                                     WHERE notifications_watched.content_type_id = {type_id}
                                       AND notifications_watched.object_id = {tbl}.id
                                       AND notifications_watched.user_id = {user_id}) > 0
                              THEN TRUE
                              ELSE FALSE
                         END""")
        sql = sql.format(type_id=type.id, tbl=model._meta.db_table, user_id=user.id)
    qs = queryset.extra(select={as_field: sql})
    return qs


def attach_total_watchers_to_queryset(queryset, as_field="total_watchers"):
    """Attach total_watchers boolean to each object of the queryset.

    :param user: A users.User object model
    :param queryset: A Django queryset object.
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = ("""SELECT count(*)
                FROM notifications_watched
               WHERE notifications_watched.content_type_id = {type_id}
                 AND notifications_watched.object_id = {tbl}.id""")
    sql = sql.format(type_id=type.id, tbl=model._meta.db_table)
    qs = queryset.extra(select={as_field: sql})
    return qs
