# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import base64
import logging
import os
import sys
import copy
from collections import OrderedDict

from taiga.base.fields import Field
from taiga.users import models as users_models

from .cache import cached_get_user_by_pk


logger = logging.getLogger(__name__)


class FileField(Field):
    def to_value(self, obj):
        if not obj:
            return None

        try:
            read_file = obj.read()
        except UnicodeEncodeError:
            logger.error("UnicodeEncodeError in %s", obj.name,
                         exc_info=sys.exc_info())
            data = ""
        else:
            data = base64.b64encode(read_file).decode('utf-8')

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
        except Exception:
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
