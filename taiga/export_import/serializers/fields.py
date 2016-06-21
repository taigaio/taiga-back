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

from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.base.fields import JsonField
from taiga.mdrender.service import render as mdrender
from taiga.users import models as users_models

from .cache import cached_get_user_by_email, cached_get_user_by_pk


class FileField(serializers.WritableField):
    read_only = False

    def to_native(self, obj):
        if not obj:
            return None

        data = base64.b64encode(obj.read()).decode('utf-8')

        return OrderedDict([
            ("data", data),
            ("name", os.path.basename(obj.name)),
        ])

    def from_native(self, data):
        if not data:
            return None

        decoded_data = b''
        # The original file was encoded by chunks but we don't really know its
        # length or if it was multiple of 3 so we must iterate over all those chunks
        # decoding them one by one
        for decoding_chunk in data['data'].split("="):
            # When encoding to base64 3 bytes are transformed into 4 bytes and
            # the extra space of the block is filled with =
            # We must ensure that the decoding chunk has a length multiple of 4 so
            # we restore the stripped '='s adding appending them until the chunk has
            # a length multiple of 4
            decoding_chunk += "=" * (-len(decoding_chunk) % 4)
            decoded_data += base64.b64decode(decoding_chunk+"=")

        return ContentFile(decoded_data, name=data['name'])


class ContentTypeField(serializers.RelatedField):
    read_only = False

    def to_native(self, obj):
        if obj:
            return [obj.app_label, obj.model]
        return None

    def from_native(self, data):
        try:
            return ContentType.objects.get_by_natural_key(*data)
        except Exception:
            return None


class RelatedNoneSafeField(serializers.RelatedField):
    def field_from_native(self, data, files, field_name, into):
        if self.read_only:
            return

        try:
            if self.many:
                try:
                    # Form data
                    value = data.getlist(field_name)
                    if value == [''] or value == []:
                        raise KeyError
                except AttributeError:
                    # Non-form data
                    value = data[field_name]
            else:
                value = data[field_name]
        except KeyError:
            if self.partial:
                return
            value = self.get_default_value()

        key = self.source or field_name
        if value in self.null_values:
            if self.required:
                raise ValidationError(self.error_messages['required'])
            into[key] = None
        elif self.many:
            into[key] = [self.from_native(item) for item in value if self.from_native(item) is not None]
        else:
            into[key] = self.from_native(value)


class UserRelatedField(RelatedNoneSafeField):
    read_only = False

    def to_native(self, obj):
        if obj:
            return obj.email
        return None

    def from_native(self, data):
        try:
            return cached_get_user_by_email(data)
        except users_models.User.DoesNotExist:
            return None


class UserPkField(serializers.RelatedField):
    read_only = False

    def to_native(self, obj):
        try:
            user = cached_get_user_by_pk(obj)
            return user.email
        except users_models.User.DoesNotExist:
            return None

    def from_native(self, data):
        try:
            user = cached_get_user_by_email(data)
            return user.pk
        except users_models.User.DoesNotExist:
            return None


class CommentField(serializers.WritableField):
    read_only = False

    def field_from_native(self, data, files, field_name, into):
        super().field_from_native(data, files, field_name, into)
        into["comment_html"] = mdrender(self.context['project'], data.get("comment", ""))


class ProjectRelatedField(serializers.RelatedField):
    read_only = False
    null_values = (None, "")

    def __init__(self, slug_field, *args, **kwargs):
        self.slug_field = slug_field
        super().__init__(*args, **kwargs)

    def to_native(self, obj):
        if obj:
            return getattr(obj, self.slug_field)
        return None

    def from_native(self, data):
        try:
            kwargs = {self.slug_field: data, "project": self.context['project']}
            return self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise ValidationError(_("{}=\"{}\" not found in this project".format(self.slug_field, data)))


class HistoryUserField(JsonField):
    def to_native(self, obj):
        if obj is None or obj == {}:
            return []
        try:
            user = cached_get_user_by_pk(obj['pk'])
        except users_models.User.DoesNotExist:
            user = None
        return (UserRelatedField().to_native(user), obj['name'])

    def from_native(self, data):
        if data is None:
            return {}

        if len(data) < 2:
            return {}

        user = UserRelatedField().from_native(data[0])

        if user:
            pk = user.pk
        else:
            pk = None

        return {"pk": pk, "name": data[1]}


class HistoryValuesField(JsonField):
    def to_native(self, obj):
        if obj is None:
            return []
        if "users" in obj:
            obj['users'] = list(map(UserPkField().to_native, obj['users']))
        return obj

    def from_native(self, data):
        if data is None:
            return []
        if "users" in data:
            data['users'] = list(map(UserPkField().from_native, data['users']))
        return data


class HistoryDiffField(JsonField):
    def to_native(self, obj):
        if obj is None:
            return []

        if "assigned_to" in obj:
            obj['assigned_to'] = list(map(UserPkField().to_native, obj['assigned_to']))

        return obj

    def from_native(self, data):
        if data is None:
            return []

        if "assigned_to" in data:
            data['assigned_to'] = list(map(UserPkField().from_native, data['assigned_to']))
        return data


class TimelineDataField(serializers.WritableField):
    read_only = False

    def to_native(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = cached_get_user_by_pk(new_data["user"]["id"])
            new_data["user"]["email"] = user.email
            del new_data["user"]["id"]
        except Exception:
            pass
        return new_data

    def from_native(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = cached_get_user_by_email(new_data["user"]["email"])
            new_data["user"]["id"] = user.id
            del new_data["user"]["email"]
        except users_models.User.DoesNotExist:
            pass

        return new_data
