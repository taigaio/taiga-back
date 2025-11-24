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

    class Meta:
        model = models.UserStory
        depth = 0
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner', 'kanban_order', 'tribe_gig')


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

class UpdateUserStoriesBacklogOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField(required=False)
    after_userstory_id = serializers.IntegerField(required=False)
    before_userstory_id = serializers.IntegerField(required=False)
    bulk_userstories = ListField(child=serializers.IntegerField(min_value=1))

    def validate_milestone_id(self, attrs, source):
        milestone_id = attrs.get(source, None)

        if milestone_id:
            filters = {
                "project__id": attrs["project_id"],
                "id": attrs[source]
            }

            if not Milestone.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid milestone id. The milestone must belong "
                                        "to the same project."))

        return attrs

    def validate_after_userstory_id(self, attrs, source):
        if attrs.get(source, None) is not None:
            filters = {
                "project__id": attrs["project_id"],
                "id": attrs[source]
            }
            milestone_id = attrs.get("milestone_id", None)
            if milestone_id:
                filters["milestone__id"] = milestone_id
            else:
                filters["milestone__isnull"] = True

            if not UserStory.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid user story id to move after. The user story must belong "
                                        "to the same project and milestone."))

        return attrs

    def validate_before_userstory_id(self, attrs, source):
        before_userstory_id = attrs.get(source, None)
        after_userstory_id = attrs.get("after_userstory_id", None)

        if after_userstory_id and before_userstory_id:
            raise ValidationError(_("You can't use after and before at the same time."))
        elif before_userstory_id is not None:
            filters = {
                "project__id": attrs["project_id"],
                "id": attrs[source]
            }
            milestone_id = attrs.get("milestone_id", None)
            if milestone_id:
                filters["milestone__id"] = milestone_id
            else:
                filters["milestone__isnull"] = True

            if not UserStory.objects.filter(**filters).exists():
                raise ValidationError(_("Invalid user story id to move before. The user story must belong "
                                        "to the same project and milestone."))

        return attrs

    def validate_bulk_userstories(self, attrs, source):
        filters = {
            "project__id": attrs["project_id"],
            "id__in": attrs[source]
        }

        if models.UserStory.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("Invalid user story ids. All stories must belong to the same project."))

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

class StoryAnalysisValidator(ProjectExistsValidator, validators.Validator):
    """
    Validator for the AI story analysis endpoint.
    
    Checks for a valid project_id and a non-empty text field.
    """
    
    # 1. 检查项目ID
    # project_id = serializers.IntegerField(
    #    required=True,
    #    help_text=_("The ID of the project.")
    # )
    
    # 2. 检查 text 字段
    text = serializers.CharField(
        required=True,
        help_text=_("The natural language requirement text to be analyzed.")
    )

    def validate(self, attrs):
        """
        Cross-field validation.
        """
        
        # 'project_id' 的存在性和有效性已由 ProjectExistsValidator 和
        # 'required=True' 处理。
        
        # 'text' 的存在性 (required=True) 和空字符串 (allow_blank=False) 
        # 已经由字段本身处理。
        
        # 我们只需要添加一个检查，确保 'text' 不仅仅是空白字符 (例如 "   ")。
        text = attrs.get("text") 
        
        if text and not text.strip():
            # 如果 text 字段存在但 strip() 后为空，则引发错误
            raise ValidationError({"text": _("This field may not be blank.")})
            
        return attrs