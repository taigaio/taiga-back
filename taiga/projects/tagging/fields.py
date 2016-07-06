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
from django.utils.translation import ugettext_lazy as _

from taiga.base.api import serializers
from taiga.base.exceptions import ValidationError

import re


class TagsAndTagsColorsField(serializers.WritableField):
    """
    Pickle objects serializer fior stories, tasks and issues tags.
    """
    def __init__(self, *args, **kwargs):
        def _validate_tag_field(value):
            # Valid field:
            #    - ["tag1", "tag2", "tag3"...]
            #    - ["tag1", ["tag2", None], ["tag3", "#ccc"], [tag4, #cccccc]...]
            for tag in value:
                if isinstance(tag, str):
                    continue

                if isinstance(tag, (list, tuple)) and len(tag) == 2:
                    name = tag[0]
                    color = tag[1]

                    if isinstance(name, str):
                        if color is None:
                            continue

                        if isinstance(color, str) and re.match('^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$', color):
                            continue

                        raise ValidationError(_("Invalid tag '{value}'. The color is not a "
                                                "valid HEX color or null.").format(value=tag))

                raise ValidationError(_("Invalid tag '{value}'. it must be the name or a pair "
                                        "'[\"name\", \"hex color/\" | null]'.").format(value=tag))

        super().__init__(*args, **kwargs)
        self.validators.append(_validate_tag_field)

    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class TagsField(serializers.WritableField):
    """
    Pickle objects serializer for tags names.
    """
    def __init__(self, *args, **kwargs):
        def _validate_tag_field(value):
            for tag in value:
                if isinstance(tag, str):
                    continue
                raise ValidationError(_("Invalid tag '{value}'. It must be the tag name.").format(value=tag))

        super().__init__(*args, **kwargs)
        self.validators.append(_validate_tag_field)

    def to_native(self, obj):
        return obj

    def from_native(self, data):
        return data


class TagsColorsField(serializers.WritableField):
    """
    PgArray objects serializer.
    """
    widget = widgets.Textarea

    def to_native(self, obj):
        return dict(obj)

    def from_native(self, data):
        return list(data.items())
