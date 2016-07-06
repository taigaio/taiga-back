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

from django.db.models import Q
from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.exceptions import ValidationError
from taiga.base.fields import JsonField
from taiga.base.fields import PgArrayField
from taiga.users.validators import RoleExistsValidator

from .tagging.fields import TagsField

from . import models
from . import services


class DuplicatedNameInProjectValidator:

    def validate_name(self, attrs, source):
        """
        Check the points name is not duplicated in the project on creation
        """
        model = self.opts.model
        qs = None
        # If the object exists:
        if self.object and attrs.get(source, None):
            qs = model.objects.filter(
                project=self.object.project,
                name=attrs[source]).exclude(id=self.object.id)

        if not self.object and attrs.get("project", None) and attrs.get(source, None):
            qs = model.objects.filter(project=attrs["project"], name=attrs[source])

        if qs and qs.exists():
            raise ValidationError(_("Name duplicated for the project"))

        return attrs


class ProjectExistsValidator:
    def validate_project_id(self, attrs, source):
        value = attrs[source]
        if not models.Project.objects.filter(pk=value).exists():
            msg = _("There's no project with that id")
            raise ValidationError(msg)
        return attrs


class UserStoryStatusExistsValidator:
    def validate_status_id(self, attrs, source):
        value = attrs[source]
        if not models.UserStoryStatus.objects.filter(pk=value).exists():
            msg = _("There's no user story status with that id")
            raise ValidationError(msg)
        return attrs


class TaskStatusExistsValidator:
    def validate_status_id(self, attrs, source):
        value = attrs[source]
        if not models.TaskStatus.objects.filter(pk=value).exists():
            msg = _("There's no task status with that id")
            raise ValidationError(msg)
        return attrs


######################################################
# Custom values for selectors
######################################################

class PointsValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.Points


class UserStoryStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.UserStoryStatus


class TaskStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.TaskStatus


class SeverityValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.Severity


class PriorityValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.Priority


class IssueStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.IssueStatus


class IssueTypeValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.IssueType


######################################################
# Members
######################################################

class MembershipValidator(validators.ModelValidator):
    email = serializers.EmailField(required=True)

    class Meta:
        model = models.Membership
        # IMPORTANT: Maintain the MembershipAdminSerializer Meta up to date
        # with this info (excluding here user_email and email)
        read_only_fields = ("user",)
        exclude = ("token", "email")

    def validate_email(self, attrs, source):
        project = attrs.get("project", None)
        if project is None:
            project = self.object.project

        email = attrs[source]

        qs = models.Membership.objects.all()

        # If self.object is not None, the serializer is in update
        # mode, and for it, it should exclude self.
        if self.object:
            qs = qs.exclude(pk=self.object.pk)

        qs = qs.filter(Q(project_id=project.id, user__email=email) |
                       Q(project_id=project.id, email=email))

        if qs.count() > 0:
            raise ValidationError(_("Email address is already taken"))

        return attrs

    def validate_role(self, attrs, source):
        project = attrs.get("project", None)
        if project is None:
            project = self.object.project

        role = attrs[source]

        if project.roles.filter(id=role.id).count() == 0:
            raise ValidationError(_("Invalid role for the project"))

        return attrs

    def validate_is_admin(self, attrs, source):
        project = attrs.get("project", None)
        if project is None:
            project = self.object.project

        if (self.object and self.object.user):
            if self.object.user.id == project.owner_id and not attrs[source]:
                raise ValidationError(_("The project owner must be admin."))

            if not services.project_has_valid_admins(project, exclude_user=self.object.user):
                raise ValidationError(
                    _("At least one user must be an active admin for this project.")
                )

        return attrs


class MembershipAdminValidator(MembershipValidator):
    class Meta:
        model = models.Membership
        # IMPORTANT: Maintain the MembershipSerializer Meta up to date
        # with this info (excluding there user_email and email)
        read_only_fields = ("user",)
        exclude = ("token",)


class MemberBulkValidator(RoleExistsValidator, validators.Validator):
    email = serializers.EmailField()
    role_id = serializers.IntegerField()


class MembersBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    bulk_memberships = MemberBulkValidator(many=True)
    invitation_extra_text = serializers.CharField(required=False, max_length=255)


######################################################
# Projects
######################################################

class ProjectValidator(validators.ModelValidator):
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    tags = TagsField(default=[], required=False)

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "slug", "blocked_code", "owner")


######################################################
# Project Templates
######################################################

class ProjectTemplateValidator(validators.ModelValidator):
    default_options = JsonField(required=False, label=_("Default options"))
    us_statuses = JsonField(required=False, label=_("User story's statuses"))
    points = JsonField(required=False, label=_("Points"))
    task_statuses = JsonField(required=False, label=_("Task's statuses"))
    issue_statuses = JsonField(required=False, label=_("Issue's statuses"))
    issue_types = JsonField(required=False, label=_("Issue's types"))
    priorities = JsonField(required=False, label=_("Priorities"))
    severities = JsonField(required=False, label=_("Severities"))
    roles = JsonField(required=False, label=_("Roles"))

    class Meta:
        model = models.ProjectTemplate
        read_only_fields = ("created_date", "modified_date")


######################################################
# Project order bulk serializers
######################################################

class UpdateProjectOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    order = serializers.IntegerField()
