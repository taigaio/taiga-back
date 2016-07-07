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

from django.forms import widgets
from django.utils.translation import ugettext as _
from taiga.base.api import serializers, ISO_8601
from taiga.base.api.settings import api_settings

import serpy


####################################################################
# DRF Serializer fields (OLD)
####################################################################
# NOTE: This should be in other place, for example taiga.base.api.serializers


class JsonField(serializers.WritableField):
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


class I18NJsonField(Field):
    """
    Json objects serializer.
    """
    def __init__(self, i18n_fields=(), *args, **kwargs):
        super(I18NJsonField, self).__init__(*args, **kwargs)
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
