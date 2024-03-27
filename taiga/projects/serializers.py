# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext as _

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField, I18NField

from taiga.permissions import services as permissions_services
from taiga.users.services import get_photo_url, get_user_photo_url
from taiga.users.gravatar import get_gravatar_id, get_user_gravatar_id
from taiga.users.serializers import UserBasicInfoSerializer

from taiga.permissions.services import calculate_permissions
from taiga.permissions.services import is_project_admin, is_project_owner

from . import services
from .notifications.choices import NotifyLevel


######################################################
# Custom values for selectors
######################################################

class BaseDueDateSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    by_default = Field()
    days_to_due = Field()
    color = Field()
    project = Field(attr="project_id")


class EpicStatusSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()
    project = Field(attr="project_id")


class UserStoryStatusSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    slug = Field()
    order = Field()
    is_closed = Field()
    is_archived = Field()
    color = Field()
    wip_limit = Field()
    project = Field(attr="project_id")


class PointsSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    value = Field()
    project = Field(attr="project_id")


class _SwimlaneStatusSerializer(serializers.LightSerializer):
    id = MethodField()
    name = MethodField()
    slug = MethodField()
    order = MethodField()
    is_closed = MethodField()
    is_archived = MethodField()
    color = MethodField()
    wip_limit = Field()
    swimlane_userstory_status_id = Field(attr="id")

    def get_id(self, obj): return obj.status.id
    def get_name(self, obj): return _(obj.status.name)
    def get_slug(self, obj): return obj.status.slug
    def get_order(self, obj): return obj.status.order
    def get_is_closed(self, obj): return obj.status.is_closed
    def get_is_archived(self, obj): return obj.status.is_archived
    def get_color(self, obj): return obj.status.color


class SwimlaneSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    project = Field(attr="project_id")
    statuses = _SwimlaneStatusSerializer(many=True, attr="statuses.all", call=True)


class SwimlaneUserStoryStatusSerializer(serializers.LightSerializer):
    id = Field()
    status = Field(attr="status_id")
    swimlane = Field(attr="swimlane_id")
    wip_limit = Field()


class UserStoryDueDateSerializer(BaseDueDateSerializer):
    pass


class TaskStatusSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()
    project = Field(attr="project_id")


class TaskDueDateSerializer(BaseDueDateSerializer):
    pass


class SeveritySerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    color = Field()
    project = Field(attr="project_id")


class PrioritySerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    color = Field()
    project = Field(attr="project_id")


class IssueStatusSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()
    project = Field(attr="project_id")


class IssueTypeSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    order = Field()
    color = Field()
    project = Field(attr="project_id")


class IssueDueDateSerializer(BaseDueDateSerializer):
    pass


######################################################
# Members
######################################################

class MembershipDictSerializer(serializers.LightDictSerializer):
    role = Field()
    role_name = Field()
    full_name = Field()
    full_name_display = MethodField()
    is_active = Field()
    id = Field()
    color = Field()
    username = Field()
    photo = MethodField()
    gravatar_id = MethodField()

    def get_full_name_display(self, obj):
        return obj["full_name"] or obj["username"] or obj["email"]

    def get_photo(self, obj):
        return get_photo_url(obj['photo'])

    def get_gravatar_id(self, obj):
        return get_gravatar_id(obj['email'])


class MembershipSerializer(serializers.LightSerializer):
    id = Field()
    user = Field(attr="user_id")
    project = Field(attr="project_id")
    role = Field(attr="role_id")
    is_admin = Field()
    created_at = Field()
    invited_by = Field(attr="invited_by_id")
    invitation_extra_text = Field()
    user_order = Field()
    role_name = MethodField()
    full_name = MethodField()
    is_user_active = MethodField()
    color = MethodField()
    photo = MethodField()
    gravatar_id = MethodField()
    project_name = MethodField()
    project_slug = MethodField()
    invited_by = UserBasicInfoSerializer()
    is_owner = MethodField()

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_full_name(self, obj):
        return obj.user.get_full_name() if obj.user else None

    def get_is_user_active(self, obj):
        return obj.user.is_active if obj.user else False

    def get_color(self, obj):
        return obj.user.color if obj.user else None

    def get_photo(self, obj):
        return get_user_photo_url(obj.user)

    def get_gravatar_id(self, obj):
        return get_user_gravatar_id(obj.user)

    def get_project_name(self, obj):
        return obj.project.name if obj and obj.project else ""

    def get_project_slug(self, obj):
        return obj.project.slug if obj and obj.project else ""

    def get_is_owner(self, obj):
        return (obj and obj.user_id and obj.project_id and obj.project.owner_id and
                obj.user_id == obj.project.owner_id)


class MembershipAdminSerializer(MembershipSerializer):
    email = Field()
    user_email = MethodField()

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    # IMPORTANT: Maintain the MembershipSerializer Meta up to date
    # with this info (excluding there user_email and email)


######################################################
# Projects
######################################################

class ProjectSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    slug = Field()
    description = Field()
    created_date = Field()
    modified_date = Field()
    owner = MethodField()
    members = MethodField()
    total_milestones = Field()
    total_story_points = Field()
    is_contact_activated = Field()
    is_epics_activated = Field()
    is_backlog_activated = Field()
    is_kanban_activated = Field()
    is_wiki_activated = Field()
    is_issues_activated = Field()
    videoconferences = Field()
    videoconferences_extra_data = Field()
    creation_template = Field(attr="creation_template_id")
    is_private = Field()
    anon_permissions = Field()
    public_permissions = Field()
    is_featured = Field()
    is_looking_for_people = Field()
    looking_for_people_note = Field()
    blocked_code = Field()
    totals_updated_datetime = Field()
    total_fans = Field()
    total_fans_last_week = Field()
    total_fans_last_month = Field()
    total_fans_last_year = Field()
    total_activity = Field()
    total_activity_last_week = Field()
    total_activity_last_month = Field()
    total_activity_last_year = Field()

    tags = Field()
    tags_colors = MethodField()

    default_epic_status = Field(attr="default_epic_status_id")
    default_points = Field(attr="default_points_id")
    default_us_status = Field(attr="default_us_status_id")
    default_task_status = Field(attr="default_task_status_id")
    default_priority = Field(attr="default_priority_id")
    default_severity = Field(attr="default_severity_id")
    default_issue_status = Field(attr="default_issue_status_id")
    default_issue_type = Field(attr="default_issue_type_id")
    default_swimlane = Field(attr="default_swimlane_id")

    my_permissions = MethodField()

    i_am_owner = MethodField()
    i_am_admin = MethodField()
    i_am_member = MethodField()

    notify_level = MethodField()
    total_closed_milestones = MethodField()

    is_watcher = MethodField()
    total_watchers = MethodField()

    logo_small_url = MethodField()
    logo_big_url = MethodField()

    is_fan = Field(attr="is_fan_attr")

    my_homepage = MethodField()

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
            user_ids = [m.get("id") for m in obj.members_attr if m["id"] is not None]
            if not user.is_anonymous and user.id in user_ids:
                return True

        return False

    def get_tags_colors(self, obj):
        return dict(obj.tags_colors)

    def get_my_permissions(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return calculate_permissions(is_authenticated=user.is_authenticated,
                                         is_superuser=user.is_superuser,
                                         is_member=self.get_i_am_member(obj),
                                         is_admin=self.get_i_am_admin(obj),
                                         role_permissions=obj.my_role_permissions_attr,
                                         anon_permissions=obj.anon_permissions,
                                         public_permissions=obj.public_permissions)
        return []

    def get_owner(self, obj):
        return UserBasicInfoSerializer(obj.owner).data

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
        return np is not None and np != NotifyLevel.none

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

    def get_my_homepage(self, obj):
        assert hasattr(obj, "my_homepage_attr"), "instance must have a my_homepage_attr attribute"
        if obj.my_homepage_attr is None:
            return False

        return obj.my_homepage_attr


class ProjectDetailSerializer(ProjectSerializer):
    epic_statuses = Field(attr="epic_statuses_attr")
    swimlanes = Field(attr="swimlanes_attr")
    us_statuses = Field(attr="userstory_statuses_attr")
    us_duedates = Field(attr="userstory_duedates_attr")
    points = Field(attr="points_attr")
    task_statuses = Field(attr="task_statuses_attr")
    task_duedates = Field(attr="task_duedates_attr")
    issue_statuses = Field(attr="issue_statuses_attr")
    issue_types = Field(attr="issue_types_attr")
    issue_duedates = Field(attr="issue_duedates_attr")
    priorities = Field(attr="priorities_attr")
    severities = Field(attr="severities_attr")
    epic_custom_attributes = Field(attr="epic_custom_attributes_attr")
    userstory_custom_attributes = Field(attr="userstory_custom_attributes_attr")
    task_custom_attributes = Field(attr="task_custom_attributes_attr")
    issue_custom_attributes = Field(attr="issue_custom_attributes_attr")
    roles = Field(attr="roles_attr")
    members = MethodField()
    total_memberships = MethodField()
    is_out_of_owner_limits = MethodField()

    # Admin fields
    is_private_extra_info = MethodField()
    max_memberships = MethodField()
    epics_csv_uuid = Field()
    userstories_csv_uuid = Field()
    tasks_csv_uuid = Field()
    issues_csv_uuid = Field()
    transfer_token = Field()
    milestones = MethodField()

    def get_milestones(self, obj):
        assert hasattr(obj, "milestones_attr"), "instance must have a milestones_attr attribute"
        if obj.milestones_attr is None:
            return []

        return obj.milestones_attr

    def to_value(self, instance):
        # Name attributes must be translated
        for attr in ["epic_statuses_attr", "userstory_statuses_attr",
                     "userstory_duedates_attr", "points_attr",
                     "task_statuses_attr", "task_duedates_attr",
                     "issue_statuses_attr", "issue_types_attr",
                     "issue_duedates_attr", "priorities_attr",
                     "severities_attr", "epic_custom_attributes_attr",
                     "userstory_custom_attributes_attr",
                     "task_custom_attributes_attr",
                     "issue_custom_attributes_attr", "roles_attr",
                     "swimlanes_attr"]:

            assert hasattr(instance, attr), "instance must have a {} attribute".format(attr)
            val = getattr(instance, attr)
            if val is None:
                continue

            for elem in val:
                elem["name"] = _(elem["name"])

        ret = super().to_value(instance)

        admin_fields = [
            "epics_csv_uuid", "userstories_csv_uuid", "tasks_csv_uuid", "issues_csv_uuid",
            "is_private_extra_info", "max_memberships", "transfer_token",
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

        return MembershipDictSerializer([m for m in obj.members_attr if m['id'] is not None], many=True).data

    def get_total_memberships(self, obj):
        if obj.members_attr is None:
            return 0

        return len(obj.members_attr)

    def get_is_out_of_owner_limits(self, obj):
        return services.check_if_project_is_out_of_owner_limits(obj)

    def get_is_private_extra_info(self, obj):
        return services.check_if_project_privacy_can_be_changed(obj)

    def get_max_memberships(self, obj):
        return services.get_max_memberships_for_project(obj)


class ProjectLightSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    slug = Field()
    description = Field()
    created_date = Field()
    modified_date = Field()
    owner = MethodField()
    members = MethodField()
    total_milestones = Field()
    total_story_points = Field()
    is_contact_activated = Field()
    is_epics_activated = Field()
    is_backlog_activated = Field()
    is_kanban_activated = Field()
    is_wiki_activated = Field()
    is_issues_activated = Field()
    videoconferences = Field()
    videoconferences_extra_data = Field()
    creation_template = Field(attr="creation_template_id")
    is_private = Field()
    anon_permissions = Field()
    public_permissions = Field()
    is_featured = Field()
    is_looking_for_people = Field()
    looking_for_people_note = Field()
    blocked_code = Field()
    totals_updated_datetime = Field()
    total_fans = Field()
    total_fans_last_week = Field()
    total_fans_last_month = Field()
    total_fans_last_year = Field()
    total_activity = Field()
    total_activity_last_week = Field()
    total_activity_last_month = Field()
    total_activity_last_year = Field()

    tags = Field()
    tags_colors = MethodField()

    default_epic_status = Field(attr="default_epic_status_id")
    default_points = Field(attr="default_points_id")
    default_us_status = Field(attr="default_us_status_id")
    default_task_status = Field(attr="default_task_status_id")
    default_priority = Field(attr="default_priority_id")
    default_severity = Field(attr="default_severity_id")
    default_issue_status = Field(attr="default_issue_status_id")
    default_issue_type = Field(attr="default_issue_type_id")
    default_swimlane = Field(attr="default_swimlane_id")

    my_permissions = MethodField()

    i_am_owner = MethodField()
    i_am_admin = MethodField()
    i_am_member = MethodField()

    is_watcher = MethodField()
    total_watchers = MethodField()

    logo_small_url = MethodField()

    is_fan = Field(attr="is_fan_attr")

    my_homepage = MethodField()

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
            user_ids = [m.get("id") for m in obj.members_attr if m["id"] is not None]
            if not user.is_anonymous and user.id in user_ids:
                return True

        return False

    def get_tags_colors(self, obj):
        return dict(obj.tags_colors)

    def get_my_permissions(self, obj):
        if "request" in self.context:
            user = self.context["request"].user
            return calculate_permissions(is_authenticated=user.is_authenticated,
                                         is_superuser=user.is_superuser,
                                         is_member=self.get_i_am_member(obj),
                                         is_admin=self.get_i_am_admin(obj),
                                         role_permissions=obj.my_role_permissions_attr,
                                         anon_permissions=obj.anon_permissions,
                                         public_permissions=obj.public_permissions)
        return []

    def get_owner(self, obj):
        return UserBasicInfoSerializer(obj.owner).data

    def get_i_am_owner(self, obj):
        if "request" in self.context:
            return is_project_owner(self.context["request"].user, obj)
        return False

    def get_i_am_admin(self, obj):
        if "request" in self.context:
            return is_project_admin(self.context["request"].user, obj)
        return False

    def get_is_watcher(self, obj):
        assert hasattr(obj, "notify_policies_attr"), "instance must have a notify_policies_attr attribute"
        np = self.get_notify_level(obj)
        return np is not None and np != NotifyLevel.none

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

    def get_my_homepage(self, obj):
        assert hasattr(obj, "my_homepage_attr"), "instance must have a my_homepage_attr attribute"
        if obj.my_homepage_attr is None:
            return False

        return obj.my_homepage_attr


######################################################
# Project Templates
######################################################
class ProjectTemplateSerializer(serializers.LightSerializer):
    id = Field()
    name = I18NField()
    slug = Field()
    description = I18NField()
    order = Field()
    created_date = Field()
    modified_date = Field()
    default_owner_role = Field()
    is_contact_activated = Field()
    is_epics_activated = Field()
    is_backlog_activated = Field()
    is_kanban_activated = Field()
    is_wiki_activated = Field()
    is_issues_activated = Field()
    videoconferences = Field()
    videoconferences_extra_data = Field()
    default_options = Field()
    epic_statuses = Field()
    us_statuses = Field()
    points = Field()
    task_statuses = Field()
    issue_statuses = Field()
    issue_types = Field()
    priorities = Field()
    severities = Field()
    roles = Field()
