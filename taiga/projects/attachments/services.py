# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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
