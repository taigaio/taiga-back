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

from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import PgArrayField
from taiga.projects.milestones.validators import MilestoneExistsValidator
from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.validators import ProjectExistsValidator
from . import models


class TaskExistsValidator:
    def validate_task_id(self, attrs, source):
        value = attrs[source]
        if not models.Task.objects.filter(pk=value).exists():
            msg = _("There's no task with that id")
            raise ValidationError(msg)
        return attrs


class TaskValidator(WatchersValidator, EditableWatchedResourceSerializer, validators.ModelValidator):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)

    class Meta:
        model = models.Task
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner')


class TasksBulkValidator(ProjectExistsValidator, MilestoneExistsValidator,
                         TaskExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    sprint_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    us_id = serializers.IntegerField(required=False)
    bulk_tasks = serializers.CharField()


# Order bulk validators

class _TaskOrderBulkValidator(TaskExistsValidator, validators.Validator):
    task_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateTasksOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField(required=False)
    status_id = serializers.IntegerField(required=False)
    us_id = serializers.IntegerField(required=False)
    bulk_tasks = _TaskOrderBulkValidator(many=True)
