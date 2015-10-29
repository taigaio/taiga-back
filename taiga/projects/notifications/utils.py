# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2015 Anler Hernández <hello@anler.me>
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

    :param user: A users.User object model
    :param queryset: A Django queryset object.
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
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


def attach_project_is_watcher_to_queryset(queryset, user, as_field="is_watcher"):
    """Attach is_watcher boolean to each object of the projects queryset.

    :param user: A users.User object model
    :param queryset: A Django projects queryset object.
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = ("""SELECT CASE WHEN (SELECT count(*)
                                  FROM notifications_notifypolicy
                                 WHERE notifications_notifypolicy.project_id = {tbl}.id
                                   AND notifications_notifypolicy.user_id = {user_id}
                                   AND notifications_notifypolicy.notify_level != {ignore_notify_level}) > 0

                          THEN TRUE
                          ELSE FALSE
                     END""")
    sql = sql.format(tbl=model._meta.db_table, user_id=user.id, ignore_notify_level=NotifyLevel.none)
    qs = queryset.extra(select={as_field: sql})
    return qs


def attach_project_total_watchers_attrs_to_queryset(queryset, as_field="total_watchers"):
    """Attach watching user ids to each project of the queryset.

    :param queryset: A Django projects queryset object.
    :param as_field: Attach the watchers as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)

    sql = ("""SELECT count(user_id)
                           FROM notifications_notifypolicy
                          WHERE notifications_notifypolicy.project_id = {tbl}.id
                            AND notifications_notifypolicy.notify_level != {ignore_notify_level}""")
    sql = sql.format(tbl=model._meta.db_table, ignore_notify_level=NotifyLevel.none)
    qs = queryset.extra(select={as_field: sql})

    return qs


def attach_notify_level_to_project_queryset(queryset, user):
    """
    Function that attach "notify_level" attribute on each queryset
    result for query notification level of current user for each
    project in the most efficient way.

    :param queryset: A Django queryset object.
    :param user: A User model object.

    :return: Queryset object with the additional `as_field` field.
    """
    user_id = getattr(user, "id", None) or "NULL"
    default_level = NotifyLevel.involved

    sql = strip_lines("""
    COALESCE((SELECT notifications_notifypolicy.notify_level
                FROM notifications_notifypolicy
               WHERE notifications_notifypolicy.project_id = projects_project.id
                 AND notifications_notifypolicy.user_id = {user_id}),
             {default_level})
    """)
    sql = sql.format(user_id=user_id, default_level=default_level)
    return queryset.extra(select={"notify_level": sql})
