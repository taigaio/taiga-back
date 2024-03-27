# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
