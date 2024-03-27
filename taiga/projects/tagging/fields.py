# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.forms import widgets
from django.utils.translation import gettext_lazy as _

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
                        if color is None or color == "":
                            continue

                        if isinstance(color, str) and re.match(r'^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$', color):
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
