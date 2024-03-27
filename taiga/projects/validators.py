# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.api.fields import validate_user_email_allowed_domains, InvalidEmailValidationError
from taiga.base.exceptions import ValidationError
from taiga.base.fields import JSONField
from taiga.base.fields import PgArrayField
from taiga.users.models import User, Role


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
            raise ValidationError(_("Duplicated name"))

        return attrs


class ProjectExistsValidator:
    def validate_project_id(self, attrs, source):
        value = attrs[source]
        if not models.Project.objects.filter(pk=value).exists():
            msg = _("There's no project with that id")
            raise ValidationError(msg)
        return attrs


######################################################
# Custom values for selectors
######################################################

class EpicStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.EpicStatus


class UserStoryStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.UserStoryStatus


class PointsValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.Points


class SwimlaneValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.Swimlane
        read_only_fields = ("order",)


class SwimlaneUserStoryStatusValidator(validators.ModelValidator):
    class Meta:
        model = models.SwimlaneUserStoryStatus
        read_only_fields = ("swimlane", "status")


class UserStoryDueDateValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.UserStoryDueDate


class TaskStatusValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.TaskStatus


class TaskDueDateValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.TaskDueDate


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


class IssueDueDateValidator(DuplicatedNameInProjectValidator, validators.ModelValidator):
    class Meta:
        model = models.IssueDueDate


class DueDatesCreationValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()


######################################################
# Members
######################################################

class MembershipValidator(validators.ModelValidator):
    username = serializers.CharField(required=True)

    class Meta:
        model = models.Membership
        read_only_fields = ("user", "email")

    def restore_object(self, attrs, instance=None):
        username = attrs.pop("username", None)
        obj = super(MembershipValidator, self).restore_object(attrs, instance=instance)
        obj.username = username
        return obj

    def _validate_member_doesnt_exist(self, attrs, email):
        project = attrs.get("project", None if self.object is None else self.object.project)
        if project is None:
            return attrs

        qs = models.Membership.objects.all()

        # If self.object is not None, the serializer is in update
        # mode, and for it, it should exclude self.
        if self.object:
            qs = qs.exclude(pk=self.object.pk)

        qs = qs.filter(Q(project_id=project.id, user__email=email) |
                       Q(project_id=project.id, email=email))

        if qs.count() > 0:
            raise ValidationError(_("The user yet exists in the project"))

    def validate_project(self, attrs, source):
        # Create only
        if self.object is not None and self.object.project != attrs.get("project"):
            raise ValidationError(_("Invalid operation"))

        return attrs

    def validate_role(self, attrs, source):
        project = attrs.get("project", None if self.object is None else self.object.project)
        if project is None:
            return attrs

        role = attrs[source]

        if project.roles.filter(id=role.id).count() == 0:
            raise ValidationError(_("Invalid role for the project"))

        return attrs

    def validate_username(self, attrs, source):
        username = attrs.get(source, None)
        try:
            validate_user_email_allowed_domains(username)

        except ValidationError:
            # If the validation comes from a request let's check the user is a valid contact
            request = self.context.get("request", None)
            if request is not None and request.user.is_authenticated:
                valid_usernames = request.user.contacts_visible_by_user(request.user).values_list("username", flat=True)
                if username not in valid_usernames:
                    raise ValidationError(_("The user must be a valid contact"))

        user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        if user is not None:
            email = user.email
            self.user = user

        else:
            email = username

        self.email = email
        self._validate_member_doesnt_exist(attrs, email)
        return attrs

    def validate_is_admin(self, attrs, source):
        project = attrs.get("project", None if self.object is None else self.object.project)
        if project is None:
            return attrs

        if (self.object and self.object.user):
            if self.object.user.id == project.owner_id and not attrs[source]:
                raise ValidationError(_("The project owner must be admin."))

            if not services.project_has_valid_admins(project, exclude_user=self.object.user):
                raise ValidationError(
                    _("At least one user must be an active admin for this project.")
                )

        return attrs

    def validate(self, attrs):
        request = self.context.get("request", None)
        if request is not None and request.user.is_authenticated and not request.user.verified_email:
            raise ValidationError(_("To add members to a project, first you have to verify your email address"))

        return super().validate(attrs)

    def is_valid(self):
        errors = super().is_valid()
        if hasattr(self, "email") and self.object is not None:
            self.object.email = self.email

        if hasattr(self, "user") and self.object is not None:
            self.object.user = self.user

        return errors


class _MemberBulkValidator(validators.Validator):
    username = serializers.CharField()
    role_id = serializers.IntegerField()

    def validate_username(self, attrs, source):
        username = attrs.get(source)
        try:
            validate_user_email_allowed_domains(username)
        except InvalidEmailValidationError:
            # If the validation comes from a request let's check the user is a valid contact
            request = self.context.get("request", None)
            if request is not None and request.user.is_authenticated:
                all_usernames = request.user.contacts_visible_by_user(request.user).values_list("username", flat=True)
                valid_usernames = set(all_usernames)
                if username not in valid_usernames:
                    raise ValidationError(_("The user must be a valid contact"))

        return attrs


class MembersBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    bulk_memberships = _MemberBulkValidator(many=True)
    invitation_extra_text = serializers.CharField(required=False, max_length=255)

    def validate_bulk_memberships(self, attrs, source):
        project_id = attrs["project_id"]
        role_ids = [r["role_id"] for r in attrs["bulk_memberships"]]

        if Role.objects.filter(project_id=project_id, id__in=role_ids).count() != len(set(role_ids)):
            raise ValidationError(_("Invalid role ids. All roles must belong to the same project."))

        return attrs


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
    default_options = JSONField(required=False, label=_("Default options"))
    us_statuses = JSONField(required=False, label=_("User story's statuses"))
    points = JSONField(required=False, label=_("Points"))
    task_statuses = JSONField(required=False, label=_("Task's statuses"))
    issue_statuses = JSONField(required=False, label=_("Issue's statuses"))
    issue_types = JSONField(required=False, label=_("Issue's types"))
    priorities = JSONField(required=False, label=_("Priorities"))
    severities = JSONField(required=False, label=_("Severities"))
    roles = JSONField(required=False, label=_("Roles"))

    class Meta:
        model = models.ProjectTemplate
        read_only_fields = ("created_date", "modified_date")


######################################################
# Project order bulk validators
######################################################

class UpdateProjectOrderBulkValidator(ProjectExistsValidator, validators.Validator):
    project_id = serializers.IntegerField()
    order = serializers.IntegerField()


######################################################
# Project duplication validator
######################################################


class DuplicateProjectMemberValidator(validators.Validator):
    id = serializers.IntegerField()


class DuplicateProjectValidator(validators.Validator):
    name = serializers.CharField()
    description = serializers.CharField()
    is_private = serializers.BooleanField()
    users = DuplicateProjectMemberValidator(many=True)
