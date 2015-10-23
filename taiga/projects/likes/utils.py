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


def attach_total_fans_to_queryset(queryset, as_field="total_fans"):
    """Attach likes count to each object of the queryset.

    Because of laziness of like objects creation, this makes much simpler and more efficient to
    access to liked-object number of likes.

    (The other way was to do it in the serializer with some try/except blocks and additional
    queries)

    :param queryset: A Django queryset object.
    :param as_field: Attach the likes-count as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = """SELECT coalesce(SUM(total_fans), 0) FROM (
                SELECT coalesce(likes_likes.count, 0) total_fans
                  FROM likes_likes
                 WHERE likes_likes.content_type_id = {type_id}
                   AND likes_likes.object_id = {tbl}.id
          ) as e"""

    sql = sql.format(type_id=type.id, tbl=model._meta.db_table)
    qs = queryset.extra(select={as_field: sql})
    return qs


def attach_is_fan_to_queryset(user, queryset, as_field="is_fan"):
    """Attach is_like boolean to each object of the queryset.

    Because of laziness of like objects creation, this makes much simpler and more efficient to
    access to likes-object and check if the curren user like it.

    (The other way was to do it in the serializer with some try/except blocks and additional
    queries)

    :param user: A users.User object model
    :param queryset: A Django queryset object.
    :param as_field: Attach the boolean as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = ("""SELECT CASE WHEN (SELECT count(*)
                                  FROM likes_like
                                 WHERE likes_like.content_type_id = {type_id}
                                   AND likes_like.object_id = {tbl}.id
                                   AND likes_like.user_id = {user_id}) > 0
                          THEN TRUE
                          ELSE FALSE
                     END""")
    sql = sql.format(type_id=type.id, tbl=model._meta.db_table, user_id=user.id)
    qs = queryset.extra(select={as_field: sql})
    return qs
