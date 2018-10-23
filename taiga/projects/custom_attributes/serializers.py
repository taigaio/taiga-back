# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
