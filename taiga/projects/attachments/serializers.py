# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

from django.conf import settings

from taiga.base.api import serializers
from taiga.base.utils.thumbnails import get_thumbnail_url

from . import services
from . import models

import json
import serpy


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")
    thumbnail_card_url = serializers.SerializerMethodField("get_thumbnail_card_url")
    attached_file = serializers.FileField(required=True)

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "name", "attached_file", "size",
                  "url", "thumbnail_card_url", "description", "is_deprecated",
                  "created_date", "modified_date", "object_id", "order", "sha1")
        read_only_fields = ("owner", "created_date", "modified_date", "sha1")

    def get_url(self, obj):
        return obj.attached_file.url


    def get_thumbnail_card_url(self, obj):
        return services.get_card_image_thumbnail_url(obj)


class ListBasicAttachmentsInfoSerializerMixin(serpy.Serializer):
    """
    Assumptions:
    - The queryset has an attribute called "include_attachments" indicating if the attachments array should contain information
        about the related elements, otherwise it will be empty
    - The method attach_basic_attachments has been used to include the necessary
        json data about the attachments in the "attachments_attr" column
    """
    attachments = serpy.MethodField()

    def get_attachments(self, obj):
        include_attachments = getattr(obj, "include_attachments", False)

        if include_attachments:
            assert hasattr(obj, "attachments_attr"), "instance must have a attachments_attr attribute"

        if not include_attachments or obj.attachments_attr is None:
            return []

        for at in obj.attachments_attr:
            at["thumbnail_card_url"] = get_thumbnail_url(at["attached_file"], settings.THN_ATTACHMENT_CARD)

        return obj.attachments_attr
