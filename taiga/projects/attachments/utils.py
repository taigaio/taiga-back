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


def attach_total_attachments(queryset, as_field="total_attachments"):
    """Attach attachment count to each object of the queryset.

    :param queryset: A Django queryset object.
    :param as_field: Attach the attachments count as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """
    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)
    sql = """SELECT count(*)
                  FROM attachments_attachment
                 WHERE attachments_attachment.content_type_id = {type_id}
                   AND attachments_attachment.object_id = {tbl}.id"""

    sql = sql.format(type_id=type.id, tbl=model._meta.db_table)
    qs = queryset.extra(select={as_field: sql})
    return qs


def attach_basic_attachments(queryset, as_field="attachments_attr"):
    """Attach basic attachments info as json column to each object of the queryset.

    :param queryset: A Django user stories queryset object.
    :param as_field: Attach the role points as an attribute with this name.

    :return: Queryset object with the additional `as_field` field.
    """

    model = queryset.model
    type = apps.get_model("contenttypes", "ContentType").objects.get_for_model(model)

    sql = """SELECT json_agg(row_to_json(t))
                FROM(
                    SELECT
                        attachments_attachment.id,
                        attachments_attachment.attached_file
                    FROM attachments_attachment
                    WHERE attachments_attachment.object_id = {tbl}.id
                     AND  attachments_attachment.content_type_id = {type_id}
                     AND  attachments_attachment.is_deprecated = False
                    ORDER BY attachments_attachment.order, attachments_attachment.created_date, attachments_attachment.id) t"""

    sql = sql.format(tbl=model._meta.db_table, type_id=type.id)
    queryset = queryset.extra(select={as_field: sql})
    return queryset
