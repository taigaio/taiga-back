# Copyright (C) 2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2015 David Barragán <bameda@dbarragan.com>
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

from django.utils.translation import ugettext_lazy as _

from rest_framework.serializers import ValidationError

from taiga.base.serializers import ModelSerializer

from . import models


######################################################
# Base Serializer  Class
#######################################################

class BaseCustomAttributeSerializer(ModelSerializer):
    def validate(self, data):
        """
        Check the name is not duplicated in the project. Check when:
          - create a new one
          - update the name
          - update the project (move to another project)
        """
        data_name = data.get("name", None)
        data_project = data.get("project", None)
        if self.object:
            data_name = data_name or self.object.name
            data_project = data_project or self.object.project

        model = self.Meta.model
        qs = model.objects.filter(project=data_project, name=data_name)
        if qs.exists():
            raise ValidationError(_("There is a custom field with the same name in this project."))

        return data


######################################################
#  Custom Field Serializers
#######################################################

class UserStoryCustomAttributeSerializer(BaseCustomAttributeSerializer):
    class Meta:
        model = models.UserStoryCustomAttribute


class TaskCustomAttributeSerializer(BaseCustomAttributeSerializer):
    class Meta:
        model = models.TaskCustomAttribute


class IssueCustomAttributeSerializer(BaseCustomAttributeSerializer):
    class Meta:
        model = models.IssueCustomAttribute
