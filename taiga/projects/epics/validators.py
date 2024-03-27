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
from taiga.projects.mixins.validators import AssignedToValidator
from taiga.projects.notifications.mixins import EditableWatchedResourceSerializer
from taiga.projects.notifications.validators import WatchersValidator
from taiga.projects.tagging.fields import TagsAndTagsColorsField
from taiga.projects.validators import ProjectExistsValidator
from . import models


class EpicExistsValidator:
    def validate_epic_id(self, attrs, source):
        value = attrs[source]
        if not models.Epic.objects.filter(pk=value).exists():
            msg = _("There's no epic with that id")
            raise ValidationError(msg)
        return attrs


class EpicValidator(AssignedToValidator, WatchersValidator, EditableWatchedResourceSerializer,
                    validators.ModelValidator):
    tags = TagsAndTagsColorsField(default=[], required=False)
    external_reference = PgArrayField(required=False)

    class Meta:
        model = models.Epic
        read_only_fields = ('id', 'ref', 'created_date', 'modified_date', 'owner')


class EpicsBulkValidator(ProjectExistsValidator, EpicExistsValidator,
                         validators.Validator):
    project_id = serializers.IntegerField()
    status_id = serializers.IntegerField(required=False)
    bulk_epics = serializers.CharField()


class CreateRelatedUserStoriesBulkValidator(ProjectExistsValidator, EpicExistsValidator,
                                            validators.Validator):
    project_id = serializers.IntegerField()
    bulk_userstories = serializers.CharField()


class EpicRelatedUserStoryValidator(validators.ModelValidator):
    class Meta:
        model = models.RelatedUserStory
        read_only_fields = ('id',)
