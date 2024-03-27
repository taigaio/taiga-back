# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
