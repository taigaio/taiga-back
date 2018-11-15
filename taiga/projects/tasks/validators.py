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

from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import PgArrayField
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.validators import AssignedToValidator
from taiga.projects.models import TaskStatus
from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.userstories.models import UserStory
from taiga.projects.validators import ProjectExistsValidator

from . import models


class TaskValidator(AssignedToValidator, WatchersValidator, EditableWatchedResourceSerializer,
                    validators.ModelValidator):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)

    class Meta:
        model = models.Task
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner')


class TasksBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    us_id = serializers.IntegerField(required=False)
    bulk_tasks = serializers.CharField()

    def validate_milestone_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not Milestone.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid milestone id."))

        return attrs

    def validate_status_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not TaskStatus.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid task status id."))

        return attrs

    def validate_us_id(self, attrs, source):
        filters = {"project__id": attrs["project_id"]}

        if "milestone_id" in attrs:
            filters["milestone__id"] = attrs["milestone_id"]

        filters["id"] = attrs["us_id"]

        if not UserStory.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid user story id."))

        return attrs


# Order bulk validators

class _TaskOrderBulkValidator(validators.Validator):
    task_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateTasksOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    us_id = serializers.IntegerField(required=False)
    milestone_id = serializers.IntegerField(required=False)
    bulk_tasks = _TaskOrderBulkValidator(many=True)

    def validate_status_id(self, attrs, source):
        filters = {"project__id": attrs["project_id"]}
        filters["id"] = attrs[source]

        if not TaskStatus.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid task status id. The status must belong to "
                                    "the same project."))

        return attrs

    def validate_us_id(self, attrs, source):
        filters = {"project__id": attrs["project_id"]}

        if "milestone_id" in attrs:
            filters["milestone__id"] = attrs["milestone_id"]

        filters["id"] = attrs[source]

        if not UserStory.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid user story id. The user story must belong to "
                                    "the same project."))

        return attrs

    def validate_milestone_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not Milestone.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid milestone id. The milestone must belong to "
                                    "the same project."))

        return attrs

    def validate_bulk_tasks(self, attrs, source):
        filters = {"project__id": attrs["project_id"]}
        if "status_id" in attrs:
            filters["status__id"] = attrs["status_id"]
        if "us_id" in attrs:
            filters["user_story__id"] = attrs["us_id"]
        if "milestone_id" in attrs:
            filters["milestone__id"] = attrs["milestone_id"]

        filters["id__in"] = [t["task_id"] for t in attrs[source]]

        if models.Task.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("Invalid task ids. All tasks must belong to the same project and, "
                                    "if it exists, to the same status, user story and/or milestone."))

        return attrs


# Milestone bulk validators

class _TaskMilestoneBulkValidator(validators.Validator):
    task_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateMilestoneBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    bulk_tasks = _TaskMilestoneBulkValidator(many=True)

    def validate_milestone_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }
        if not Milestone.objects.filter(**filters).exists():
            raise ValidationError(_("The milestone isn't valid for the project"))
        return attrs

    def validate_bulk_tasks(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id__in": [task["task_id"] for task in attrs[source]]
        }

        if models.Task.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("All the tasks must be from the same project"))

        return attrs
