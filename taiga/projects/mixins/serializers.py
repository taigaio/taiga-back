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

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.users.serializers import UserBasicInfoSerializer

from django.utils.translation import ugettext as _


class CachedUsersSerializerMixin(serializers.LightSerializer):
    def to_value(self, instance):
        self._serialized_users = {}
        return super().to_value(instance)

    def get_user_extra_info(self, user):
        if user is None:
            return None

        serialized_user = self._serialized_users.get(user.id, None)
        if serialized_user is None:
            serialized_user = UserBasicInfoSerializer(user).data
            self._serialized_users[user.id] = serialized_user

        return serialized_user


class OwnerExtraInfoSerializerMixin(CachedUsersSerializerMixin):
    owner = Field(attr="owner_id")
    owner_extra_info = MethodField()

    def get_owner_extra_info(self, obj):
        return self.get_user_extra_info(obj.owner)


class AssignedToExtraInfoSerializerMixin(CachedUsersSerializerMixin):
    assigned_to = Field(attr="assigned_to_id")
    assigned_to_extra_info = MethodField()

    def get_assigned_to_extra_info(self, obj):
        return self.get_user_extra_info(obj.assigned_to)


class StatusExtraInfoSerializerMixin(serializers.LightSerializer):
    status = Field(attr="status_id")
    status_extra_info = MethodField()

    def to_value(self, instance):
        self._serialized_status = {}
        return super().to_value(instance)

    def get_status_extra_info(self, obj):
        if obj.status_id is None:
            return None

        serialized_status = self._serialized_status.get(obj.status_id, None)
        if serialized_status is None:
            serialized_status = {
                "name": _(obj.status.name),
                "color": obj.status.color
            }
            self._serialized_status[obj.status_id] = serialized_status

        return serialized_status
