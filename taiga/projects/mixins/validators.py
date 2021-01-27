# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
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

from django.utils.translation import ugettext as _

from taiga.base.api import validators, serializers
from taiga.base.exceptions import ValidationError
from taiga.projects.models import Membership
from taiga.projects.validators import ProjectExistsValidator


class AssignedToValidator:
    def validate_assigned_to(self, attrs, source):
        assigned_to = attrs[source]
        project = (attrs.get("project", None) or
                   getattr(self.object, "project", None))

        if assigned_to and project:
            filters = {
                "project_id": project.id,
                "user_id": assigned_to.id
            }

            if not Membership.objects.filter(**filters).exists():
                raise ValidationError(_("The user must be a project member."))

        return attrs


class PromoteToUserStoryValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
