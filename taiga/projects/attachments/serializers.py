# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from os import path
import hashlib

from django.conf import settings

from taiga.base.api import serializers

from taiga.base.utils.urls import reverse

from . import models


class AttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField("get_url")
    attached_file = serializers.FileField(required=True)

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "name", "attached_file", "size", "url",
                  "description", "is_deprecated", "created_date", "modified_date",
                  "object_id", "order", "sha1")
        read_only_fields = ("owner", "created_date", "modified_date", "sha1")

    def get_url(self, obj):
        return obj.attached_file.url