# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from typing import List, Optional, Union

from urllib.parse import parse_qs, urldefrag

from django.apps import apps
from django.db import connection
from django.conf import settings

from psycopg2.extras import execute_values

from taiga.base.utils.thumbnails import get_thumbnail_url, get_thumbnail

from . import models

# Refresh feature

REFRESH_PARAM = "_taiga-refresh"


def get_attachment_by_id(project_id, attachment_id):
    model_cls = apps.get_model("attachments", "Attachment")
    try:
        obj = model_cls.objects.select_related("content_type").get(id=attachment_id)
    except model_cls.DoesNotExist:
        return None

    if not obj.content_object or obj.content_object.project_id != project_id:
        return None

    return obj


def generate_refresh_fragment(attachment, type_=""):
    if not attachment:
        return ''
    type_ = attachment.content_type.model if not type_ else type_
    return "{}={}:{}".format(REFRESH_PARAM, type_, attachment.id)


def extract_refresh_id(url):
    if not url:
        return False, False
    _, frag = urldefrag(url)
    if not frag:
        return False, False
    qs = parse_qs(frag)
    if not qs:
        return False, False
    ref = qs.get(REFRESH_PARAM, False)
    if not ref:
        return False, False
    type_, _, id_ = ref[0].partition(":")
    try:
        return type_, int(id_)
    except ValueError:
        return False, False


def url_is_an_attachment(url: str, base=None) -> "Union[str, None]":
    if not url:
        return None
    return url if url.startswith(base or settings.MEDIA_URL) else None


# Thumbnail services

def get_timeline_image_thumbnail_name(attachment):
    if attachment.attached_file:
        thumbnail = get_thumbnail(attachment.attached_file, settings.THN_ATTACHMENT_TIMELINE)
        return thumbnail.name if thumbnail else None
    return None


def get_card_image_thumbnail_url(attachment):
    if attachment.attached_file:
        return get_thumbnail_url(attachment.attached_file, settings.THN_ATTACHMENT_CARD)
    return None


def get_attachment_image_preview_url(attachment):
    if attachment.attached_file:
        return get_thumbnail_url(attachment.attached_file, settings.THN_ATTACHMENT_PREVIEW)
    return None


# Sorting attachments

def update_order_in_bulk(item: Union["Epic", "UserStory", "Task", "Issue", "WikiPage"],
                         bulk_attachments: List[int],
                         after_attachment: Optional[models.Attachment] = None):
    """
    Updates the order of the attachments specified adding the extra updates
    needed to keep consistency.

     - `bulk_attachments` should be a list of attachment IDs
    """

    # get item attachments
    attachments = item.attachments.all()

    # exclude moved attachments
    attachments = attachments.exclude(id__in=bulk_attachments)

    # if after_attachment, exclude it and get only elements after it:
    if after_attachment:
        attachments = (attachments.exclude(id=after_attachment.id)
                                  .filter(order__gte=after_attachment.order))

    # sort and get only ids
    attachment_ids = (attachments.order_by("order", "id")
                                  .values_list('id', flat=True))

    # append moved user stories
    attachment_ids = bulk_attachments + list(attachment_ids)

    # calculate the start order
    if after_attachment:
        # order start after the after_attachment order
        start_order = after_attachment.order + 1
    else:
        # move at the beggining of the column if there is no after and before
        start_order = 1

    # prepare rest of data
    total_attachments = len(attachment_ids)
    attachment_orders = range(start_order, start_order + total_attachments)

    data = tuple(zip(attachment_ids,
                     attachment_orders))

    # execute query for update order
    sql = """
    UPDATE attachments_attachment
       SET "order" = tmp.new_order::BIGINT
      FROM (VALUES %s) AS tmp (id, new_order)
     WHERE tmp.id = attachments_attachment.id
    """

    with connection.cursor() as cursor:
        execute_values(cursor, sql, data)

    # Generate response with modified info
    res = ({
        "id": id,
        "order": order
    } for (id, order) in data)
    return res
