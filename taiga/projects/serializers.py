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
from django.db.models import Q

from taiga.base.api import serializers
from taiga.base.fields import JsonField
from taiga.base.fields import PgArrayField
from taiga.base.fields import TagsField
from taiga.base.fields import TagsColorsField

from taiga.projects.notifications.choices import NotifyLevel
from taiga.users.services import get_photo_or_gravatar_url
from taiga.users.serializers import UserSerializer
from taiga.users.serializers import UserBasicInfoSerializer
from taiga.users.serializers import ProjectRoleSerializer
from taiga.users.validators import RoleExistsValidator

from taiga.permissions.service import get_user_project_permissions
from taiga.permissions.service import is_project_admin, is_project_owner
from taiga.projects.mixins.serializers import ValidateDuplicatedNameInProjectMixin

from . import models
from . import services
from .notifications.mixins import WatchedResourceModelSerializer
from .validators import ProjectExistsValidator
from .custom_attributes.serializers import UserStoryCustomAttributeSerializer
from .custom_attributes.serializers import TaskCustomAttributeSerializer
from .custom_attributes.serializers import IssueCustomAttributeSerializer
from .likes.mixins.serializers import FanResourceSerializerMixin


######################################################
## Custom values for selectors
######################################################

class PointsSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.Points
        i18n_fields = ("name",)


class UserStoryStatusSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.UserStoryStatus
        i18n_fields = ("name",)


class BasicUserStoryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserStoryStatus
        i18n_fields = ("name",)
        fields = ("name", "color")


class TaskStatusSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.TaskStatus
        i18n_fields = ("name",)


class BasicTaskStatusSerializerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskStatus
        i18n_fields = ("name",)
        fields = ("name", "color")


class SeveritySerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.Severity
        i18n_fields = ("name",)


class PrioritySerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.Priority
        i18n_fields = ("name",)


class IssueStatusSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.IssueStatus
        i18n_fields = ("name",)


class BasicIssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IssueStatus
        i18n_fields = ("name",)
        fields = ("name", "color")


class IssueTypeSerializer(ValidateDuplicatedNameInProjectMixin):
    class Meta:
        model = models.IssueType
        i18n_fields = ("name",)


######################################################
## Members
######################################################

class MembershipSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', required=False, read_only=True, i18n=True)
    full_name = serializers.CharField(source='user.get_full_name', required=False, read_only=True)
    user_email = serializers.EmailField(source='user.email', required=False, read_only=True)
    is_user_active = serializers.BooleanField(source='user.is_active', required=False,
                                              read_only=True)
    email = serializers.EmailField(required=True)
    color = serializers.CharField(source='user.color', required=False, read_only=True)
    photo = serializers.SerializerMethodField("get_photo")
    project_name = serializers.SerializerMethodField("get_project_name")
    project_slug = serializers.SerializerMethodField("get_project_slug")
    invited_by = UserBasicInfoSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField("get_is_owner")

    class Meta:
        model = models.Membership
        # IMPORTANT: Maintain the MembershipAdminSerializer Meta up to date
        # with this info (excluding here user_email and email)
        read_only_fields = ("user",)
        exclude = ("token", "user_email", "email")

    def get_photo(self, project):
        return get_photo_or_gravatar_url(project.user)

    def get_project_name(self, obj):
        return obj.project.name if obj and obj.project else ""

    def get_project_slug(self, obj):
        return obj.project.slug if obj and obj.project else ""

    def get_is_owner(self, obj):
        return (obj and obj.user_id and obj.project_id and obj.project.owner_id and
                obj.user_id == obj.project.owner_id)

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
            raise serializers.ValidationError(_("Email address is already taken"))

        return attrs

    def validate_role(self, attrs, source):
        project = attrs.get("project", None)
        if project is None:
            project = self.object.project

        role = attrs[source]

        if project.roles.filter(id=role.id).count() == 0:
            raise serializers.ValidationError(_("Invalid role for the project"))

        return attrs

    def validate_is_admin(self, attrs, source):
        project = attrs.get("project", None)
        if project is None:
            project = self.object.project

        if (self.object and self.object.user):
            if self.object.user.id == project.owner_id and attrs[source] != True:
                raise serializers.ValidationError(_("The project owner must be admin."))

            if not services.project_has_valid_admins(project, exclude_user=self.object.user):
                raise serializers.ValidationError(_("At least one user must be an active admin for this project."))

        return attrs


class MembershipAdminSerializer(MembershipSerializer):
    class Meta:
        model = models.Membership
        # IMPORTANT: Maintain the MembershipSerializer Meta up to date
        # with this info (excluding there user_email and email)
        read_only_fields = ("user",)
        exclude = ("token",)


class MemberBulkSerializer(RoleExistsValidator, serializers.Serializer):
    email = serializers.EmailField()
    role_id = serializers.IntegerField()


class MembersBulkSerializer(ProjectExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    bulk_memberships = MemberBulkSerializer(many=True)
    invitation_extra_text = serializers.CharField(required=False, max_length=255)


class ProjectMemberSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    full_name_display = serializers.CharField(source='user.get_full_name', read_only=True)
    color = serializers.CharField(source='user.color', read_only=True)
    photo = serializers.SerializerMethodField("get_photo")
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True, i18n=True)

    class Meta:
        model = models.Membership
        exclude = ("project", "email", "created_at", "token", "invited_by", "invitation_extra_text",
                   "user_order")

    def get_photo(self, membership):
        return get_photo_or_gravatar_url(membership.user)


######################################################
## Projects
######################################################

class ProjectSerializer(FanResourceSerializerMixin, WatchedResourceModelSerializer,
                        serializers.ModelSerializer):
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    my_permissions = serializers.SerializerMethodField("get_my_permissions")

    owner = UserBasicInfoSerializer(read_only=True)
    i_am_owner = serializers.SerializerMethodField("get_i_am_owner")
    i_am_admin = serializers.SerializerMethodField("get_i_am_admin")
    i_am_member = serializers.SerializerMethodField("get_i_am_member")

    tags = TagsField(default=[], required=False)
    tags_colors = TagsColorsField(required=False)

    notify_level = serializers.SerializerMethodField("get_notify_level")
    total_closed_milestones = serializers.SerializerMethodField("get_total_closed_milestones")
    total_watchers = serializers.SerializerMethodField("get_total_watchers")

    logo_small_url = serializers.SerializerMethodField("get_logo_small_url")
    logo_big_url = serializers.SerializerMethodField("get_logo_big_url")

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "slug", "blocked_code")
        exclude = ("logo", "last_us_ref", "last_task_ref", "last_issue_ref",
                   "issues_csv_uuid", "tasks_csv_uuid", "userstories_csv_uuid",
                   "transfer_token")

    def get_my_permissions(self, obj):
        if "request" in self.context:
            return get_user_project_permissions(self.context["request"].user, obj)
        return []

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_project_owner(self.context["request"].user, obj)
        return False

    def get_i_am_admin(self, obj):
        if "request" in self.context:
            return is_project_admin(self.context["request"].user, obj)
        return False

    def get_i_am_member(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            if not user.is_anonymous() and user.cached_membership_for_project(obj):
                return True
        return False

    def get_total_closed_milestones(self, obj):
        # The "closed_milestone" attribute can be attached in the get_queryset method of the viewset.
        qs_closed_milestones = getattr(obj, "closed_milestones", None)
        if qs_closed_milestones is not None:
            return len(qs_closed_milestones)

        return obj.milestones.filter(closed=True).count()

    def get_notify_level(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return user.is_authenticated() and user.get_notify_level(obj)

        return None

    def get_total_watchers(self, obj):
        # The "valid_notify_policies" attribute can be attached in the get_queryset method of the viewset.
        qs_valid_notify_policies = getattr(obj, "valid_notify_policies", None)
        if qs_valid_notify_policies is not None:
            return len(qs_valid_notify_policies)

        return obj.notify_policies.exclude(notify_level=NotifyLevel.none).count()

    def get_logo_small_url(self, obj):
        return services.get_logo_small_thumbnail_url(obj)

    def get_logo_big_url(self, obj):
        return services.get_logo_big_thumbnail_url(obj)


class ProjectDetailSerializer(ProjectSerializer):
    us_statuses = UserStoryStatusSerializer(many=True, required=False)       # User Stories
    points = PointsSerializer(many=True, required=False)

    task_statuses = TaskStatusSerializer(many=True, required=False)          # Tasks

    issue_statuses = IssueStatusSerializer(many=True, required=False)
    issue_types = IssueTypeSerializer(many=True, required=False)
    priorities = PrioritySerializer(many=True, required=False)               # Issues
    severities = SeveritySerializer(many=True, required=False)

    userstory_custom_attributes = UserStoryCustomAttributeSerializer(source="userstorycustomattributes",
                                                                     many=True, required=False)
    task_custom_attributes = TaskCustomAttributeSerializer(source="taskcustomattributes",
                                                           many=True, required=False)
    issue_custom_attributes = IssueCustomAttributeSerializer(source="issuecustomattributes",
                                                             many=True, required=False)

    roles = ProjectRoleSerializer(source="roles", many=True, read_only=True)
    members = serializers.SerializerMethodField(method_name="get_members")
    total_memberships = serializers.SerializerMethodField(method_name="get_total_memberships")

    def get_members(self, obj):
        qs = obj.memberships.filter(user__isnull=False)
        qs = qs.extra(select={"complete_user_name":"concat(full_name, username)"})
        qs = qs.order_by("complete_user_name")
        qs = qs.select_related("role", "user")
        serializer = ProjectMemberSerializer(qs, many=True)
        return serializer.data

    def get_total_memberships(self, obj):
        return services.get_total_project_memberships(obj)


class ProjectDetailAdminSerializer(ProjectDetailSerializer):
    is_private_extra_info = serializers.SerializerMethodField(method_name="get_is_private_extra_info")
    max_memberships = serializers.SerializerMethodField(method_name="get_max_memberships")

    class Meta:
        model = models.Project
        read_only_fields = ("created_date", "modified_date", "slug", "blocked_code")
        exclude = ("logo", "last_us_ref", "last_task_ref", "last_issue_ref")

    def get_is_private_extra_info(self, obj):
        return services.check_if_project_privacity_can_be_changed(obj)

    def get_max_memberships(self, obj):
        return services.get_max_memberships_for_project(obj)


######################################################
## Liked
######################################################

class LikedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'slug']



######################################################
## Project Templates
######################################################

class ProjectTemplateSerializer(serializers.ModelSerializer):
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
        i18n_fields = ("name", "description")

######################################################
## Project order bulk serializers
######################################################

class UpdateProjectOrderBulkSerializer(ProjectExistsValidator, serializers.Serializer):
    project_id = serializers.IntegerField()
    order = serializers.IntegerField()
