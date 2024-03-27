# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.fields import JSONField, Field
from taiga.base.api import serializers


######################################################
# Custom Attribute Serializer
#######################################################

class BaseCustomAttributeSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    description = Field()
    type = Field()
    order = Field()
    project = Field(attr="project_id")
    extra = Field()
    created_date = Field()
    modified_date = Field()


class EpicCustomAttributeSerializer(BaseCustomAttributeSerializer):
    pass


class UserStoryCustomAttributeSerializer(BaseCustomAttributeSerializer):
    pass


class TaskCustomAttributeSerializer(BaseCustomAttributeSerializer):
    pass


class IssueCustomAttributeSerializer(BaseCustomAttributeSerializer):
    pass


######################################################
# Custom Attribute Serializer
#######################################################
class BaseCustomAttributesValuesSerializer(serializers.LightSerializer):
    attributes_values = Field()
    version = Field()


class EpicCustomAttributesValuesSerializer(BaseCustomAttributesValuesSerializer):
    epic = Field(attr="epic.id")


class UserStoryCustomAttributesValuesSerializer(BaseCustomAttributesValuesSerializer):
    user_story = Field(attr="user_story.id")


class TaskCustomAttributesValuesSerializer(BaseCustomAttributesValuesSerializer):
    task = Field(attr="task.id")


class IssueCustomAttributesValuesSerializer(BaseCustomAttributesValuesSerializer):
    issue = Field(attr="issue.id")
