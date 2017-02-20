# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
        return obj.attached_file.url

    def get_thumbnail_card_url(self, obj):
        return services.get_card_image_thumbnail_url(obj)

    def get_preview_url(self, obj):
        if obj.name.endswith(".psd"):
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
