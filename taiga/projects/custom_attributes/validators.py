# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _

from taiga.base.fields import JSONField
from taiga.base.exceptions import ValidationError
from taiga.base.api.validators import ModelValidator

from . import models


######################################################
# Custom Attribute Validator
#######################################################

class BaseCustomAttributeValidator(ModelValidator):
    class Meta:
        read_only_fields = ('id',)
        exclude = ('created_date', 'modified_date')

    def _validate_integrity_between_project_and_name(self, attrs, source):
        """
        Check the name is not duplicated in the project. Check when:
          - create a new one
          - update the name
          - update the project (move to another project)
        """
        data_id = attrs.get("id", None)
        data_name = attrs.get("name", None)
        data_project = attrs.get("project", None)

        if self.object:
            data_id = data_id or self.object.id
            data_name = data_name or self.object.name
            data_project = data_project or self.object.project

        model = self.Meta.model
        qs = (model.objects.filter(project=data_project, name=data_name)
                           .exclude(id=data_id))
        if qs.exists():
            raise ValidationError(_("Already exists one with the same name."))

        return attrs

    def validate_name(self, attrs, source):
        return self._validate_integrity_between_project_and_name(attrs, source)

    def validate_project(self, attrs, source):
        return self._validate_integrity_between_project_and_name(attrs, source)


class EpicCustomAttributeValidator(BaseCustomAttributeValidator):
    class Meta(BaseCustomAttributeValidator.Meta):
        model = models.EpicCustomAttribute


class UserStoryCustomAttributeValidator(BaseCustomAttributeValidator):
    class Meta(BaseCustomAttributeValidator.Meta):
        model = models.UserStoryCustomAttribute


class TaskCustomAttributeValidator(BaseCustomAttributeValidator):
    class Meta(BaseCustomAttributeValidator.Meta):
        model = models.TaskCustomAttribute


class IssueCustomAttributeValidator(BaseCustomAttributeValidator):
    class Meta(BaseCustomAttributeValidator.Meta):
        model = models.IssueCustomAttribute


######################################################
# Custom Attribute Validator
#######################################################


class BaseCustomAttributesValuesValidator(ModelValidator):
    attributes_values = JSONField(source="attributes_values", label="attributes values")
    _custom_attribute_model = None
    _container_field = None

    class Meta:
        exclude = ("id",)

    def validate_attributes_values(self, attrs, source):
        # values must be a dict
        data_values = attrs.get("attributes_values", None)
        if self.object:
            data_values = (data_values or self.object.attributes_values)

        if type(data_values) is not dict:
            raise ValidationError(_("Invalid content. It must be {\"key\": \"value\",...}"))

        # Values keys must be in the container object project
        data_container = attrs.get(self._container_field, None)
        if data_container:
            project_id = data_container.project_id
        elif self.object:
            project_id = getattr(self.object, self._container_field).project_id
        else:
            project_id = None

        values_ids = list(data_values.keys())
        qs = self._custom_attribute_model.objects.filter(project=project_id,
                                                         id__in=values_ids)
        if qs.count() != len(values_ids):
            raise ValidationError(_("It contains invalid custom fields."))

        return attrs


class EpicCustomAttributesValuesValidator(BaseCustomAttributesValuesValidator):
    _custom_attribute_model = models.EpicCustomAttribute
    _container_model = "epics.Epic"
    _container_field = "epic"

    class Meta(BaseCustomAttributesValuesValidator.Meta):
        model = models.EpicCustomAttributesValues


class UserStoryCustomAttributesValuesValidator(BaseCustomAttributesValuesValidator):
    _custom_attribute_model = models.UserStoryCustomAttribute
    _container_model = "userstories.UserStory"
    _container_field = "user_story"

    class Meta(BaseCustomAttributesValuesValidator.Meta):
        model = models.UserStoryCustomAttributesValues


class TaskCustomAttributesValuesValidator(BaseCustomAttributesValuesValidator, ModelValidator):
    _custom_attribute_model = models.TaskCustomAttribute
    _container_field = "task"

    class Meta(BaseCustomAttributesValuesValidator.Meta):
        model = models.TaskCustomAttributesValues


class IssueCustomAttributesValuesValidator(BaseCustomAttributesValuesValidator, ModelValidator):
    _custom_attribute_model = models.IssueCustomAttribute
    _container_field = "issue"

    class Meta(BaseCustomAttributesValuesValidator.Meta):
        model = models.IssueCustomAttributesValues
