# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError

from . import services
from . import fields

import re


class ProjectTagValidator(validators.Validator):
    def __init__(self, *args, **kwargs):
        # Don't pass the extra project arg
        self.project = kwargs.pop("project")

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)


class CreateTagValidator(ProjectTagValidator):
    tag = serializers.CharField()
    color = serializers.CharField(required=False)

    def validate_tag(self, attrs, source):
        tag = attrs.get(source, None)
        if services.tag_exist_for_project_elements(self.project, tag):
            raise ValidationError(_("This tag already exists."))

        return attrs

    def validate_color(self, attrs, source):
        color = attrs.get(source, None)
        if color and not re.match(r'^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$', color):
            raise ValidationError(_("The color is not a valid HEX color."))

        return attrs


class EditTagTagValidator(ProjectTagValidator):
    from_tag = serializers.CharField()
    to_tag = serializers.CharField(required=False)
    color = serializers.CharField(required=False)

    def validate_from_tag(self, attrs, source):
        tag = attrs.get(source, None)
        if not services.tag_exist_for_project_elements(self.project, tag):
            raise ValidationError(_("The tag doesn't exist."))

        return attrs

    def validate_to_tag(self, attrs, source):
        tag = attrs.get(source, None)
        if services.tag_exist_for_project_elements(self.project, tag):
            raise ValidationError(_("This tag already exists."))

        return attrs

    def validate_color(self, attrs, source):
        color = attrs.get(source, None)
        if color and not re.match(r'^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$', color):
            raise ValidationError(_("The color is not a valid HEX color."))

        return attrs

    def validate(self, data):
        if "to_tag" not in data:
            data["to_tag"] = data.get("from_tag")

        if "color" not in data:
            data["color"] = dict(self.project.tags_colors).get(data.get("from_tag"))

        return data


class DeleteTagValidator(ProjectTagValidator):
    tag = serializers.CharField()

    def validate_tag(self, attrs, source):
        tag = attrs.get(source, None)
        if not services.tag_exist_for_project_elements(self.project, tag):
            raise ValidationError(_("The tag doesn't exist."))

        return attrs


class MixTagsValidator(ProjectTagValidator):
    from_tags = fields.TagsField()
    to_tag = serializers.CharField()

    def validate_from_tags(self, attrs, source):
        tags = attrs.get(source, None)
        for tag in tags:
            if not services.tag_exist_for_project_elements(self.project, tag):
                raise ValidationError(_("The tag doesn't exist."))

        return attrs

    def validate_to_tag(self, attrs, source):
        tag = attrs.get(source, None)
        if not services.tag_exist_for_project_elements(self.project, tag):
            raise ValidationError(_("The tag doesn't exist."))

        return attrs
