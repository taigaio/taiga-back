# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.forms import widgets
from django.utils.translation import gettext as _
from taiga.base.api import serializers, ISO_8601
from taiga.base.api.settings import api_settings

import serpy


####################################################################
# DRF Serializer fields (OLD)
####################################################################
# NOTE: This should be in other place, for example taiga.base.api.serializers


class JSONField(serializers.WritableField):
    """
    Json objects serializer.
    """
    widget = widgets.Textarea

    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class PgArrayField(serializers.WritableField):
    """
    PgArray objects serializer.
    """
    widget = widgets.Textarea

    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class PickledObjectField(serializers.WritableField):
    """
    PickledObjectField objects serializer.
    """
    widget = widgets.Textarea

    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class WatchersField(serializers.WritableField):
    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class ListField(serializers.WritableField):
    """
    A field whose values are lists of items described by the given child. The child can
    be another field type (e.g., CharField) or a serializer. However, for serializers, you should
    instead just use it with the `many=True` option.
    """

    default_error_messages = {
        'invalid_type': _('%(value)s is not a list'),
    }
    empty = []

    def __init__(self, child=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.child = child

    def initialize(self, parent, field_name):
        super().initialize(parent, field_name)
        if self.child:
            self.child.initialize(parent, field_name)

    def to_native(self, obj):
        if self.child and obj:
            return [self.child.to_native(item) for item in obj]
        return obj

    def from_native(self, data):
        self.validate_is_list(data)
        if self.child and data:
            return [self.child.from_native(item_data) for item_data in data]
        return data

    def validate(self, value):
        super().validate(value)

        self.validate_is_list(value)

        if self.child:
            errors = {}
            for index, item in enumerate(value):
                try:
                    self.child.validate(item)
                except ValidationError as e:
                    errors[index] = e.messages

            if errors:
                raise NestedValidationError(errors)

    def run_validators(self, value):
        super().run_validators(value)

        if self.child:
            errors = {}
            for index, item in enumerate(value):
                try:
                    self.child.run_validators(item)
                except ValidationError as e:
                    errors[index] = e.messages

            if errors:
                raise NestedValidationError(errors)

    def validate_is_list(self, value):
        if value is not None and not isinstance(value, list):
            raise ValidationError(self.error_messages['invalid_type'],
                                  code='invalid_type',
                                  params={'value': value})


####################################################################
# Serpy fields (NEW)
####################################################################

class Field(serpy.Field):
    pass


class MethodField(serpy.MethodField):
    pass


class I18NField(Field):
    def to_value(self, value):
        ret = super(I18NField, self).to_value(value)
        return _(ret)


class I18NJSONField(Field):
    """
    Json objects serializer.
    """
    def __init__(self, i18n_fields=(), *args, **kwargs):
        super(I18NJSONField, self).__init__(*args, **kwargs)
        self.i18n_fields = i18n_fields

    def translate_values(self, d):
        i18n_d = {}
        if d is None:
            return d

        for key, value in d.items():
            if isinstance(value, dict):
                i18n_d[key] = self.translate_values(value)

            if key in self.i18n_fields:
                if isinstance(value, list):
                    i18n_d[key] = [e is not None and _(str(e)) or e for e in value]
                if isinstance(value, str):
                    i18n_d[key] = value is not None and _(value) or value
            else:
                i18n_d[key] = value

        return i18n_d

    def to_native(self, obj):
        i18n_obj = self.translate_values(obj)
        return i18n_obj


class FileField(Field):
    def to_value(self, value):
        if value:
            return value.name
        return None


class DateTimeField(Field):
    format = api_settings.DATETIME_FORMAT

    def to_value(self, value):
        if value is None or self.format is None:
            return value

        if self.format.lower() == ISO_8601:
            ret = value.isoformat()
            if ret.endswith("+00:00"):
                ret = ret[:-6] + "Z"
            return ret
        return value.strftime(self.format)
