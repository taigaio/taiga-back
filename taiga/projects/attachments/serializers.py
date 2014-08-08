# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from rest_framework import serializers

from taiga.base.utils.urls import reverse
from . import models


class AttachmentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField("get_name")
    url = serializers.SerializerMethodField("get_url")
    size = serializers.SerializerMethodField("get_size")

    class Meta:
        model = models.Attachment
        fields = ("id", "project", "owner", "name", "attached_file", "size", "url",
                  "description", "is_deprecated", "created_date", "modified_date",
                  "object_id", "order")
        read_only_fields = ("owner",)

    def get_name(self, obj):
        if obj.attached_file:
            return path.basename(obj.attached_file.path)
        return ""

    def get_url(self, obj):
        token = None

        url = reverse("attachment-url", kwargs={"pk": obj.pk})
        if "request" in self.context and self.context["request"].user.is_authenticated():
            user_id = self.context["request"].user.id
            token_src = "{}-{}-{}".format(settings.ATTACHMENTS_TOKEN_SALT, user_id, obj.id)
            token = hashlib.sha1(token_src.encode("utf-8"))

            return "{}?user={}&token={}".format(url, user_id, token.hexdigest())

        return url

    def get_size(self, obj):
        if obj.attached_file:
            try:
                return obj.attached_file.size
            except FileNotFoundError:
                pass
        return 0
