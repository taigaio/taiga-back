# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos Ventures SL

from urllib.parse import parse_qs, urldefrag

from django.apps import apps
from django.conf import settings

from taiga.base.utils.thumbnails import get_thumbnail_url, get_thumbnail

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
