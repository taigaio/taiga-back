# -*- coding: utf-8 -*-
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
