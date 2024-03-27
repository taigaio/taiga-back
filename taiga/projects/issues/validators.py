# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import PgArrayField
from taiga.projects.milestones.models import Milestone
from taiga.projects.mixins.validators import AssignedToValidator
from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.validators import ProjectExistsValidator

from . import models


class IssueValidator(AssignedToValidator, WatchersValidator, EditableWatchedResourceSerializer,
                     validators.ModelValidator):

    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)

    class Meta:
        model = models.Issue
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner')


class IssuesBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField(required=False)
    bulk_issues = serializers.CharField()


# Milestone bulk validators

class _IssueMilestoneBulkValidator(validators.Validator):
    issue_id = serializers.IntegerField()


class UpdateMilestoneBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    milestone_id = serializers.IntegerField()
    bulk_issues = _IssueMilestoneBulkValidator(many=True)

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
            "id__in": [issue["issue_id"] for issue in attrs[source]]
        }

        if models.Issue.objects.filter(**filters).count() != len(filters["id__in"]):
            raise ValidationError(_("All the issues must be from the same project"))

        return attrs
