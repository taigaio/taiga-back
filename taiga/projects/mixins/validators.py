# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import validators, serializers
from taiga.base.exceptions import ValidationError
from taiga.projects.models import Membership
from taiga.projects.validators import ProjectExistsValidator
from taiga.projects.milestones.models import Milestone


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


class DemoteToTaskValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    # fallback milestone when the source user story has none, to avoid an orphaned task
    milestone_id = serializers.IntegerField(required=False)

    def validate_milestone_id(self, attrs, source):
        milestone_id = attrs.get(source, None)

        if milestone_id:
            filters = {
                "project__id": attrs["project_id"],
                "id": milestone_id,
            }

            if not Milestone.objects.filter(**filters).exists():
                raise ValidationError(
                    _(
                        "Invalid milestone id. The milestone must belong "
                        "to the same project."
                    )
                )

        return attrs
