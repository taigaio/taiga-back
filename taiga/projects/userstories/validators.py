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

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import PgArrayField
from taiga.base.fields import ListField
from taiga.base.fields import PickledObjectField
from taiga.base.utils import json
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.validators import AssignedToValidator
from taiga.projects.models import UserStoryStatus, Swimlane
from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.userstories.models import UserStory
from taiga.projects.validators import ProjectExistsValidator

from . import models


class UserStoryExistsValidator:
    def validate_us_id(self, attrs, source):
        value = attrs[source]
        if not models.UserStory.objects.filter(pk=value).exists():
            msg = _("There's no user story with that id")
            raise ValidationError(msg)
        return attrs


class RolePointsField(serializers.WritableField):
    def to_native(self, obj):
        return {str(o.role.id): o.points.id for o in obj.all()}

    def from_native(self, obj):
        if isinstance(obj, dict):
            return obj
        return json.loads(obj)


class UserStoryValidator(AssignedToValidator, WatchersValidator,
                         EditableWatchedResourceSerializer, validators.ModelValidator):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)
    points = RolePointsField(source="role_points", required=False)
    tribe_gig = PickledObjectField(required=False)

    class Meta:
        model = models.UserStory
        depth = 0
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner', 'kanban_order')


class UserStoriesBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    swimlane_id = serializers.IntegerField(required=False)
    bulk_stories = serializers.CharField()

    def validate_status_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not UserStoryStatus.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid user story status id. The status must belong to "
                                    "the same project."))

        return attrs

    def validate_swimlane_id(self, attrs, source):
        if attrs.get(source, None) is not None:
            filters = {
                "project__id": attrs["project_id"],
                "id": attrs[source]
            }

            if not Swimlane.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid swimlane id. The swimlane must belong to "
                                        "the same project."))

        return attrs


# Order bulk validators

class _UserStoryOrderBulkValidator(validators.Validator):
    us_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateUserStoriesOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    milestone_id = serializers.IntegerField(required=False)
    bulk_stories = _UserStoryOrderBulkValidator(many=True)

    def validate_status_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not UserStoryStatus.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid user story status id. The status must belong "
                                    "to the same project."))

        return attrs

    def validate_milestone_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not Milestone.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid milestone id. The milistone must belong to the "
                                    "same project."))

        return attrs

    def validate_bulk_stories(self, attrs, source):
        filters = {"project__id": attrs["project_id"]}
        if "milestone_id" in attrs:
            filters["milestone__id"] = attrs["milestone_id"]

        filters["id__in"] = [us["us_id"] for us in attrs[source]]

        if models.UserStory.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("Invalid user story ids. All stories must belong to the same project "
                                    "and, if it exists, to the same status and milestone."))

        return attrs


class UpdateUserStoriesKanbanOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField()
    swimlane_id = serializers.IntegerField(required=False)
    after_userstory_id = serializers.IntegerField(required=False)
    before_userstory_id = serializers.IntegerField(required=False)
    bulk_userstories = ListField(child=serializers.IntegerField(min_value=1))

    def validate_status_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not UserStoryStatus.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid user story status id. The status must belong "
                                    "to the same project."))

        return attrs

    def validate_swimlane_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }

        if not Swimlane.objects.filter(**filters).exists():
            raise ValidationError(_("Invalid swimlane id. The swimlane must belong "
                                    "to the same project."))

        return attrs

    def validate_after_userstory_id(self, attrs, source):
        if attrs.get(source, None) is not None:
            filters = {
                "project__id": attrs["project_id"],
                "status__id": attrs["status_id"],
                "id": attrs[source]
            }
            swimlane_id = attrs.get("swimlane_id", None)
            if swimlane_id:
                filters["swimlane__id"] = swimlane_id
            else:
                filters["swimlane__isnull"] = True

            if not UserStory.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid user story id to move after. The user story must belong "
                                        "to the same project, status and swimlane."))

        return attrs

    def validate_before_userstory_id(self, attrs, source):
        before_userstory_id = attrs.get(source, None)
        after_userstory_id = attrs.get("after_userstory_id", None)

        if after_userstory_id and before_userstory_id:
            raise ValidationError(_("You can't use after and before at the same time."))
        elif before_userstory_id is not None:
            filters = {
                "project__id": attrs["project_id"],
                "status__id": attrs["status_id"],
                "id": attrs[source]
            }
            swimlane_id = attrs.get("swimlane_id", None)
            if swimlane_id:
                filters["swimlane__id"] = swimlane_id
            else:
                filters["swimlane__isnull"] = True

            if not UserStory.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid user story id to move before. The user story must belong "
                                        "to the same project, status and swimlane."))

        return attrs

    def validate_bulk_userstories(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id__in": attrs[source]
        }

        if models.UserStory.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("Invalid user story ids. All stories must belong to the same project."))

        return attrs


# Milestone bulk validators

class _UserStoryMilestoneBulkValidator(validators.Validator):
    us_id = serializers.IntegerField()
    order = serializers.IntegerField()


class UpdateMilestoneBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    bulk_stories = _UserStoryMilestoneBulkValidator(many=True)

    def validate_milestone_id(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id": attrs[source]
        }
        if not Milestone.objects.filter(**filters).exists():
            raise ValidationError(_("The milestone isn't valid for the project"))
        return attrs

    def validate_bulk_stories(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id__in": [us["us_id"] for us in attrs[source]]
        }

        if UserStory.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("All the user stories must be from the same project"))

        return attrs
