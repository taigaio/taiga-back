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

import serpy

from django.utils.translation import ugettext as _
from django.db.models import Q

from taiga.base.api import serializers
from taiga.base.fields import JsonField
from taiga.base.fields import PgArrayField

from taiga.permissions import services as permissions_services
from taiga.users.services import get_photo_or_gravatar_url
from taiga.users.serializers import UserBasicInfoSerializer
from taiga.users.serializers import ProjectRoleSerializer
from taiga.users.serializers import ListUserBasicInfoSerializer
from taiga.users.validators import RoleExistsValidator

from taiga.permissions.services import get_user_project_permissions
from taiga.permissions.services import calculate_permissions
from taiga.permissions.services import is_project_admin, is_project_owner

from . import models
from . import services
from .custom_attributes.serializers import UserStoryCustomAttributeSerializer
from .custom_attributes.serializers import TaskCustomAttributeSerializer
from .custom_attributes.serializers import IssueCustomAttributeSerializer
from .likes.mixins.serializers import FanResourceSerializerMixin
from .mixins.serializers import ValidateDuplicatedNameInProjectMixin
from .notifications.choices import NotifyLevel
from .notifications.mixins import WatchedResourceModelSerializer
from .tagging.fields import TagsField
from .tagging.fields import TagsColorsField
from .validators import ProjectExistsValidator

import serpy

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
    tags_colors = TagsColorsField(required=False, read_only=True)

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
        return obj.milestones.filter(closed=True).count()

    def get_notify_level(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return user.is_authenticated() and user.get_notify_level(obj)

        return None

    def get_total_watchers(self, obj):
        return obj.notify_policies.exclude(notify_level=NotifyLevel.none).count()

    def get_logo_small_url(self, obj):
        return services.get_logo_small_thumbnail_url(obj)

    def get_logo_big_url(self, obj):
        return services.get_logo_big_thumbnail_url(obj)


class LightProjectSerializer(serializers.LightSerializer):
    id = serpy.Field()
    name = serpy.Field()
    slug = serpy.Field()
    description = serpy.Field()
    created_date = serpy.Field()
    modified_date = serpy.Field()
    owner = serpy.MethodField()
    members = serpy.MethodField()
    total_milestones = serpy.Field()
    total_story_points = serpy.Field()
    is_backlog_activated = serpy.Field()
    is_kanban_activated = serpy.Field()
    is_wiki_activated = serpy.Field()
    is_issues_activated = serpy.Field()
    videoconferences = serpy.Field()
    videoconferences_extra_data = serpy.Field()
    creation_template = serpy.Field(attr="creation_template_id")
    is_private = serpy.Field()
    anon_permissions = serpy.Field()
    public_permissions = serpy.Field()
    is_featured = serpy.Field()
    is_looking_for_people = serpy.Field()
    looking_for_people_note = serpy.Field()
    blocked_code = serpy.Field()
    totals_updated_datetime = serpy.Field()
    total_fans = serpy.Field()
    total_fans_last_week = serpy.Field()
    total_fans_last_month = serpy.Field()
    total_fans_last_year = serpy.Field()
    total_activity = serpy.Field()
    total_activity_last_week = serpy.Field()
    total_activity_last_month = serpy.Field()
    total_activity_last_year = serpy.Field()

    tags = serpy.Field()
    tags_colors = serpy.MethodField()

    default_points = serpy.Field(attr="default_points_id")
    default_us_status = serpy.Field(attr="default_us_status_id")
    default_task_status = serpy.Field(attr="default_task_status_id")
    default_priority = serpy.Field(attr="default_priority_id")
    default_severity = serpy.Field(attr="default_severity_id")
    default_issue_status = serpy.Field(attr="default_issue_status_id")
    default_issue_type = serpy.Field(attr="default_issue_type_id")

    my_permissions = serpy.MethodField()

    i_am_owner = serpy.MethodField()
    i_am_admin = serpy.MethodField()
    i_am_member = serpy.MethodField()

    notify_level = serpy.MethodField("get_notify_level")
    total_closed_milestones = serpy.MethodField()

    is_watcher = serpy.MethodField()
    total_watchers = serpy.MethodField()

    logo_small_url = serpy.MethodField()
    logo_big_url = serpy.MethodField()

    is_fan = serpy.Field(attr="is_fan_attr")

    def get_members(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return []

        return [m.get("id") for m in obj.members_attr if m["id"] is not None]

    def get_i_am_member(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return False

        if "request" in self.context:
            user = self.context["request"].user
            if not user.is_anonymous() and user.id in [m.get("id") for m in obj.members_attr if m["id"] is not None]:
                return True

        return False

    def get_tags_colors(self, obj):
        return dict(obj.tags_colors)

    def get_my_permissions(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return calculate_permissions(
                        is_authenticated = user.is_authenticated(),
                        is_superuser = user.is_superuser,
                        is_member = self.get_i_am_member(obj),
                        is_admin = self.get_i_am_admin(obj),
                        role_permissions = obj.my_role_permissions_attr,
                        anon_permissions = obj.anon_permissions,
                        public_permissions = obj.public_permissions)
        return []

    def get_owner(self, obj):
        return ListUserBasicInfoSerializer(obj.owner).data

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_project_owner(self.context["request"].user, obj)
        return False

    def get_i_am_admin(self, obj):
        if "request" in self.context:
            return is_project_admin(self.context["request"].user, obj)
        return False

    def get_total_closed_milestones(self, obj):
        assert hasattr(obj, "closed_milestones_attr"), "instance must have a closed_milestones_attr attribute"
        return obj.closed_milestones_attr

    def get_is_watcher(self, obj):
        assert hasattr(obj, "notify_policies_attr"), "instance must have a notify_policies_attr attribute"
        np = self.get_notify_level(obj)
        return np != None and np != NotifyLevel.none

    def get_total_watchers(self, obj):
        assert hasattr(obj, "notify_policies_attr"), "instance must have a notify_policies_attr attribute"
        if obj.notify_policies_attr is None:
            return 0

        valid_notify_policies = [np for np in obj.notify_policies_attr if np["notify_level"] != NotifyLevel.none]
        return len(valid_notify_policies)

    def get_notify_level(self, obj):
        assert hasattr(obj, "notify_policies_attr"), "instance must have a notify_policies_attr attribute"
        if obj.notify_policies_attr is None:
            return None

        if "request" in self.context:
            user = self.context["request"].user
            for np in obj.notify_policies_attr:
                if np["user_id"] == user.id:
                    return np["notify_level"]

        return None

    def get_logo_small_url(self, obj):
        return services.get_logo_small_thumbnail_url(obj)

    def get_logo_big_url(self, obj):
        return services.get_logo_big_thumbnail_url(obj)


class LightProjectDetailSerializer(LightProjectSerializer):
    us_statuses = serpy.Field(attr="userstory_statuses_attr")
    points = serpy.Field(attr="points_attr")
    task_statuses = serpy.Field(attr="task_statuses_attr")
    issue_statuses = serpy.Field(attr="issue_statuses_attr")
    issue_types = serpy.Field(attr="issue_types_attr")
    priorities = serpy.Field(attr="priorities_attr")
    severities = serpy.Field(attr="severities_attr")
    userstory_custom_attributes = serpy.Field(attr="userstory_custom_attributes_attr")
    task_custom_attributes = serpy.Field(attr="task_custom_attributes_attr")
    issue_custom_attributes = serpy.Field(attr="issue_custom_attributes_attr")
    roles = serpy.Field(attr="roles_attr")
    members = serpy.MethodField()
    total_memberships = serpy.MethodField()
    is_out_of_owner_limits = serpy.MethodField()

    #Admin fields
    is_private_extra_info = serpy.MethodField()
    max_memberships = serpy.MethodField()
    issues_csv_uuid = serpy.Field()
    tasks_csv_uuid = serpy.Field()
    userstories_csv_uuid = serpy.Field()
    transfer_token = serpy.Field()

    def to_value(self, instance):
        # Name attributes must be translated
        for attr in ["userstory_statuses_attr","points_attr", "task_statuses_attr",
                     "issue_statuses_attr", "issue_types_attr", "priorities_attr",
                     "severities_attr", "userstory_custom_attributes_attr",
                     "task_custom_attributes_attr","issue_custom_attributes_attr", "roles_attr"]:

            assert hasattr(instance, attr), "instance must have a {} attribute".format(attr)
            val = getattr(instance, attr)
            if val is None:
                continue

            for elem in val:
                elem["name"] = _(elem["name"])

        ret = super().to_value(instance)

        admin_fields = [
            "is_private_extra_info", "max_memberships", "issues_csv_uuid",
            "tasks_csv_uuid", "userstories_csv_uuid", "transfer_token"
        ]

        is_admin_user = False
        if "request" in self.context:
            user = self.context["request"].user
            is_admin_user = permissions_services.is_project_admin(user, instance)

        if not is_admin_user:
            for admin_field in admin_fields:
                del(ret[admin_field])

        return ret

    def get_members(self, obj):
        assert hasattr(obj, "members_attr"), "instance must have a members_attr attribute"
        if obj.members_attr is None:
            return []

        ret = []
        for m in obj.members_attr:
            m["full_name_display"] = m["full_name"] or m["username"] or m["email"]
            del(m["email"])
            del(m["complete_user_name"])
            if not m["id"] is None:
                ret.append(m)

        return ret

    def get_total_memberships(self, obj):
        if obj.members_attr is None:
            return 0

        return len(obj.members_attr)

    def get_is_out_of_owner_limits(self, obj):
        assert hasattr(obj, "private_projects_same_owner_attr"), "instance must have a private_projects_same_owner_attr attribute"
        assert hasattr(obj, "public_projects_same_owner_attr"), "instance must have a public_projects_same_owner_attr attribute"
        return services.check_if_project_is_out_of_owner_limits(obj,
            current_memberships = self.get_total_memberships(obj),
            current_private_projects=obj.private_projects_same_owner_attr,
            current_public_projects=obj.public_projects_same_owner_attr
        )

    def get_is_private_extra_info(self, obj):
        assert hasattr(obj, "private_projects_same_owner_attr"), "instance must have a private_projects_same_owner_attr attribute"
        assert hasattr(obj, "public_projects_same_owner_attr"), "instance must have a public_projects_same_owner_attr attribute"
        return services.check_if_project_privacity_can_be_changed(obj,
            current_memberships = self.get_total_memberships(obj),
            current_private_projects=obj.private_projects_same_owner_attr,
            current_public_projects=obj.public_projects_same_owner_attr
        )

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
