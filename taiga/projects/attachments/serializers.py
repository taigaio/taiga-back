# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings

from taiga.base.api import serializers
from taiga.base.fields import MethodField, Field, FileField
from taiga.base.utils.thumbnails import get_thumbnail_url

from . import services


class AttachmentSerializer(serializers.LightSerializer):
    id = Field()
    project = Field(attr="project_id")
    owner = Field(attr="owner_id")
    name = Field()
    attached_file = FileField()
    size = Field()
    url = Field()
    description = Field()
    is_deprecated = Field()
    from_comment = Field()
    created_date = Field()
    modified_date = Field()
    object_id = Field()
    order = Field()
    sha1 = Field()
    url = MethodField("get_url")
    thumbnail_card_url = MethodField("get_thumbnail_card_url")
    preview_url = MethodField("get_preview_url")

    def get_url(self, obj):
        frag = services.generate_refresh_fragment(obj)
        return "{}#{}".format(obj.attached_file.url, frag)

    def get_thumbnail_card_url(self, obj):
        return services.get_card_image_thumbnail_url(obj)

    def get_preview_url(self, obj):
        if obj.attached_file.name.lower().endswith(".psd"):
            return services.get_attachment_image_preview_url(obj)
        return self.get_url(obj)


class BasicAttachmentsInfoSerializerMixin(serializers.LightSerializer):
    """
    Assumptions:
    - The queryset has an attribute called "include_attachments" indicating if the attachments array should contain information
        about the related elements, otherwise it will be empty
    - The method attach_basic_attachments has been used to include the necessary
        json data about the attachments in the "attachments_attr" column
    """
    attachments = MethodField()

    def get_attachments(self, obj):
        include_attachments = getattr(obj, "include_attachments", False)

        if include_attachments:
            assert hasattr(obj, "attachments_attr"), "instance must have a attachments_attr attribute"

        if not include_attachments or obj.attachments_attr is None:
            return []

        for at in obj.attachments_attr:
            at["thumbnail_card_url"] = get_thumbnail_url(at["attached_file"], settings.THN_ATTACHMENT_CARD)

        return obj.attachments_attr
