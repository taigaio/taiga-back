# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import base64
import copy

from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType

from taiga.base.api import serializers
from taiga.base.exceptions import ValidationError
from taiga.base.fields import JSONField
from taiga.mdrender.service import render as mdrender
from taiga.users import models as users_models

from .cache import cached_get_user_by_email


class FileField(serializers.WritableField):
    read_only = False

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
            decoded_data += base64.b64decode(decoding_chunk + "=")

        return ContentFile(decoded_data, name=data['name'])


class ContentTypeField(serializers.RelatedField):
    read_only = False

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

    def from_native(self, data):
        try:
            return cached_get_user_by_email(data)
        except users_models.User.DoesNotExist:
            return None


class UserPkField(serializers.RelatedField):
    read_only = False

    def from_native(self, data):
        try:
            user = cached_get_user_by_email(data)
            return user.pk
        except Exception:
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

    def from_native(self, data):
        try:
            kwargs = {self.slug_field: data, "project": self.context['project']}
            return self.queryset.get(**kwargs)
        except ObjectDoesNotExist:
            raise ValidationError(_("{}=\"{}\" not found in this project".format(self.slug_field, data)))


class HistorySnapshotField(JSONField):
    def from_native(self, data):
        if data is None:
            return {}

        owner = UserRelatedField().from_native(data.get("owner"))
        if owner:
            data["owner"] = owner.pk

        assigned_to = UserRelatedField().from_native(data.get("assigned_to"))
        if assigned_to:
            data["assigned_to"] = assigned_to.pk

        return data


class HistoryUserField(JSONField):
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


class HistoryValuesField(JSONField):
    def from_native(self, data):
        if data is None:
            return []
        if "users" in data:
            data['users'] = list(map(UserPkField().from_native, data['users']))
        return data


class HistoryDiffField(JSONField):
    def from_native(self, data):
        if data is None:
            return []

        if "assigned_to" in data:
            data['assigned_to'] = list(map(UserPkField().from_native, data['assigned_to']))
        return data


class TimelineDataField(serializers.WritableField):
    read_only = False

    def from_native(self, data):
        new_data = copy.deepcopy(data)
        try:
            user = cached_get_user_by_email(new_data["user"]["email"])
            new_data["user"]["id"] = user.id
            del new_data["user"]["email"]
        except users_models.User.DoesNotExist:
            pass

        return new_data
