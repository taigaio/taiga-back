# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from os import path

from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from rest_framework import serializers

from taiga.base.serializers import JsonField, PgArrayField, ModelSerializer, TagsColorsField
from taiga.users.models import Role, User
from taiga.users.services import get_photo_or_gravatar_url
from taiga.users.serializers import UserSerializer
from taiga.users.validators import RoleExistsValidator

from taiga.permissions.service import get_user_project_permissions, is_project_owner

from . import models
from . validators import ProjectExistsValidator


# User Stories common serializers

class PointsSerializer(ModelSerializer):
    class Meta:
        model = models.Points


class UserStoryStatusSerializer(ModelSerializer):
    class Meta:
        model = models.UserStoryStatus

    def validate_name(self, attrs, source):
        """
        Check the status name is not duplicated in the project on creation
        """
        qs = None
        # If the user story status exists:
        if self.object and attrs.get("name", None):
            qs = models.UserStoryStatus.objects.filter(project=self.object.project, name=attrs[source])

        if not self.object and attrs.get("project", None)  and attrs.get("name", None):
            qs = models.UserStoryStatus.objects.filter(project=attrs["project"], name=attrs[source])

        if qs and qs.exists():
              raise serializers.ValidationError("Name duplicated for the project")

        return attrs


# Task common serializers

class TaskStatusSerializer(ModelSerializer):
    class Meta:
        model = models.TaskStatus


# Issues common serializers

class SeveritySerializer(ModelSerializer):
    class Meta:
        model = models.Severity


class PrioritySerializer(ModelSerializer):
    class Meta:
        model = models.Priority


class IssueStatusSerializer(ModelSerializer):
    class Meta:
        model = models.IssueStatus


class IssueTypeSerializer(ModelSerializer):
    class Meta:
        model = models.IssueType


# Projects

class MembershipSerializer(ModelSerializer):
    role_name = serializers.CharField(source='role.name', required=False, read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', required=False, read_only=True)
    user_email = serializers.EmailField(source='user.email', required=False, read_only=True)
    email = serializers.EmailField(required=True)
    color = serializers.CharField(source='user.color', required=False, read_only=True)
    photo = serializers.SerializerMethodField("get_photo")
    project_name = serializers.SerializerMethodField("get_project_name")
    project_slug = serializers.SerializerMethodField("get_project_slug")
    invited_by = UserSerializer(read_only=True)

    class Meta:
        model = models.Membership
        read_only_fields = ("user",)
        exclude = ("token",)

    def get_photo(self, project):
        return get_photo_or_gravatar_url(project.user)

    def get_project_name(self, obj):
        return obj.project.name if obj and obj.project else ""

    def get_project_slug(self, obj):
        return obj.project.slug if obj and obj.project else ""

    def validate_email(self, attrs, source):
        project = attrs["project"]
        email = attrs[source]

        qs = models.Membership.objects.all()

        # If self.object is not None, the serializer is in update
        # mode, and for it, it should exclude self.
        if self.object:
            qs = qs.exclude(pk=self.object.pk)

        qs = qs.filter(Q(project_id=project.id, user__email=email) |
                       Q(project_id=project.id, email=email))

        if qs.count() > 0:
            raise serializers.ValidationError(_("Email address is already taken"))

        return attrs


class ProjectMembershipSerializer(ModelSerializer):
    role_name = serializers.CharField(source='role.name', required=False)
    full_name = serializers.CharField(source='user.get_full_name', required=False)
    color = serializers.CharField(source='user.color', required=False)
    photo = serializers.SerializerMethodField("get_photo")

    class Meta:
        model = models.Membership

    def get_photo(self, project):
        return get_photo_or_gravatar_url(project.user)


class ProjectSerializer(ModelSerializer):
    tags = PgArrayField(required=False)
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    stars = serializers.SerializerMethodField("get_stars_number")
    my_permissions = serializers.SerializerMethodField("get_my_permissions")
    i_am_owner = serializers.SerializerMethodField("get_i_am_owner")
    tags_colors = TagsColorsField(required=False)

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "owner")
        exclude = ("last_us_ref", "last_task_ref", "last_issue_ref")

    def get_stars_number(self, obj):
        # The "stars_count" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "stars_count", 0)

    def get_my_permissions(self, obj):
        if "request" in self.context:
            return get_user_project_permissions(self.context["request"].user, obj)
        return []

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_project_owner(self.context["request"].user, obj)
        return False

    def validate_total_milestones(self, attrs, source):
        """
        Check that total_milestones is not null, it's an optional parameter but
        not nullable in the model. 
        """
        value = attrs[source]
        if value is None:
            raise serializers.ValidationError("Total milestones must be major or equal to zero")
        return attrs

class ProjectDetailSerializer(ProjectSerializer):
    roles = serializers.SerializerMethodField("get_roles")
    memberships = serializers.SerializerMethodField("get_memberships")
    us_statuses = UserStoryStatusSerializer(many=True, required=False)       # User Stories
    points = PointsSerializer(many=True, required=False)
    task_statuses = TaskStatusSerializer(many=True, required=False)          # Tasks
    issue_statuses = IssueStatusSerializer(many=True, required=False)
    issue_types = IssueTypeSerializer(many=True, required=False)
    priorities = PrioritySerializer(many=True, required=False)               # Issues
    severities = SeveritySerializer(many=True, required=False)

    def get_memberships(self, obj):
        qs = obj.memberships.filter(user__isnull=False)
        qs = qs.order_by('user__full_name', 'user__username')
        qs = qs.select_related("role", "user")

        serializer = ProjectMembershipSerializer(qs, many=True)
        return serializer.data

    def get_roles(self, obj):
        serializer = ProjectRoleSerializer(obj.roles.all(), many=True)
        return serializer.data


class ProjectRoleSerializer(ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'slug', 'order', 'computable')


class RoleSerializer(ModelSerializer):
    members_count = serializers.SerializerMethodField("get_members_count")
    permissions = PgArrayField(required=False)

    class Meta:
        model = Role
        fields = ('id', 'name', 'permissions', 'computable', 'project', 'order', 'members_count')

    def get_members_count(self, obj):
        return obj.memberships.count()


class ProjectTemplateSerializer(ModelSerializer):
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


class StarredSerializer(ModelSerializer):
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'slug']


class MemberBulkSerializer(RoleExistsValidator, serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.IntegerField()


class MembersBulkSerializer(ProjectExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_memberships = MemberBulkSerializer(many=True)
    invitation_extra_text = serializers.CharField(required=False, max_length=255)
