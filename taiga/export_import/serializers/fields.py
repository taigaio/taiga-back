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

import base64
import os
import copy
from collections import OrderedDict

from taiga.base.api import serializers
from taiga.base.fields import Field
from taiga.users import models as users_models

from .cache import cached_get_user_by_pk


class FileField(Field):
    def to_value(self, obj):
        if not obj:
            return None

        data = base64.b64encode(obj.read()).decode('utf-8')

        return OrderedDict([
            ("data", data),
            ("name", os.path.basename(obj.name)),
        ])


class ContentTypeField(Field):
    def to_value(self, obj):
        if obj:
            return [obj.app_label, obj.model]
        return None


class UserRelatedField(Field):
    def to_value(self, obj):
        if obj:
            return obj.email
        return None


class UserPkField(Field):
    def to_value(self, obj):
        try:
            user = cached_get_user_by_pk(obj)
            return user.email
        except users_models.User.DoesNotExist:
            return None


class SlugRelatedField(Field):
    def __init__(self, slug_field, *args, **kwargs):
        self.slug_field = slug_field
        super().__init__(*args, **kwargs)

    def to_value(self, obj):
        if obj:
            return getattr(obj, self.slug_field)
        return None


class HistoryUserField(Field):
    def to_value(self, obj):
        if obj is None or obj == {}:
            return []
        try:
            user = cached_get_user_by_pk(obj['pk'])
        except users_models.User.DoesNotExist:
            user = None
        return (UserRelatedField().to_value(user), obj['name'])


class HistoryValuesField(Field):
    def to_value(self, obj):
        if obj is None:
            return []
        if "users" in obj:
            obj['users'] = list(map(UserPkField().to_value, obj['users']))
        return obj


class HistoryDiffField(Field):
    def to_value(self, obj):
        if obj is None:
            return []

        if "assigned_to" in obj:
            obj['assigned_to'] = list(map(UserPkField().to_value, obj['assigned_to']))

        return obj


class TimelineDataField(Field):
    def to_value(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = cached_get_user_by_pk(new_data["user"]["id"])
            new_data["user"]["email"] = user.email
            del new_data["user"]["id"]
        except Exception:
            pass
        return new_data
