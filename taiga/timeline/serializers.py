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

from django.contrib.auth import get_user_model

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.users.services import get_user_photo_url, get_user_big_photo_url
from taiga.users.gravatar import get_user_gravatar_id

from . import models


class TimelineSerializer(serializers.LightSerializer):
    data = serializers.SerializerMethodField("get_data")
    id = Field()
    content_type = Field(attr="content_type_id")
    object_id = Field()
    namespace = Field()
    event_type = Field()
    project = Field(attr="project_id")
    data = MethodField()
    data_content_type = Field(attr="data_content_type_id")
    created = Field()

    class Meta:
        model = models.Timeline

    def get_data(self, obj):
        # Updates the data user info saved if the user exists
        if hasattr(obj, "_prefetched_user"):
            user = obj._prefetched_user
        else:
            User = get_user_model()
            userData = obj.data.get("user", None)
            try:
                user = User.objects.get(id=userData["id"])
            except User.DoesNotExist:
                user = None

        if user is not None:
            obj.data["user"] = {
                "id": user.pk,
                "name": user.get_full_name(),
                "photo": get_user_photo_url(user),
                "big_photo": get_user_big_photo_url(user),
                "gravatar_id": get_user_gravatar_id(user),
                "username": user.username,
                "is_profile_visible": user.is_active and not user.is_system,
                "date_joined": user.date_joined
            }

        return obj.data
