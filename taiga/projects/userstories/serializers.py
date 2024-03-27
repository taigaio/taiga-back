# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.attachments.serializers import BasicAttachmentsInfoSerializerMixin
from taiga.projects.due_dates.serializers import DueDateSerializerMixin
from taiga.projects.mixins.serializers import AssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import OwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import StatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.tagging.serializers import TaggedInProjectResourceSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin
from taiga.projects.history.mixins import TotalCommentsSerializerMixin


class OriginItemSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()
    subject = Field()

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


class UserStoryListSerializer(ProjectExtraInfoSerializerMixin,
        VoteResourceSerializerMixin, WatchedResourceSerializer,
        OwnerExtraInfoSerializerMixin, AssignedToExtraInfoSerializerMixin,
        StatusExtraInfoSerializerMixin, BasicAttachmentsInfoSerializerMixin,
        TaggedInProjectResourceSerializer, TotalCommentsSerializerMixin,
        DueDateSerializerMixin, serializers.LightSerializer):

    id = Field()
    ref = Field()
    milestone = Field(attr="milestone_id")
    milestone_slug = MethodField()
    milestone_name = MethodField()
    project = Field(attr="project_id")
    is_closed = Field()
    points = MethodField()
    backlog_order = Field()
    sprint_order = Field()
    kanban_order = Field()
    created_date = Field()
    modified_date = Field()
    finish_date = Field()
    subject = Field()
    client_requirement = Field()
    team_requirement = Field()
    generated_from_issue = Field(attr="generated_from_issue_id")
    generated_from_task = Field(attr="generated_from_task_id")
    from_task_ref = Field()
    external_reference = Field()
    tribe_gig = Field()
    version = Field()
    watchers = Field()
    is_blocked = Field()
    blocked_note = Field()
    total_points = MethodField()
    comment = MethodField()
    origin_issue = OriginItemSerializer(attr="generated_from_issue")
    origin_task = OriginItemSerializer(attr="generated_from_task")
    epics = MethodField()
    epic_order = MethodField()
    tasks = MethodField()
    total_attachments = Field()
    swimlane = Field(attr="swimlane_id")

    assigned_users = MethodField()

    def get_assigned_users(self, obj):
        """Get the assigned of an object.

        :return: User queryset object representing the assigned users
        """
        if not obj.assigned_to:
            return set([user.id for user in obj.assigned_users.all()])

        assigned_users = [user.id for user in obj.assigned_users.all()] + \
                         [obj.assigned_to.id]

        if not assigned_users:
            return None

        return set(assigned_users)

    def get_epic_order(self, obj):
        include_epic_order = getattr(obj, "include_epic_order", False)

        if include_epic_order:
            assert hasattr(obj, "epic_order"), "instance must have a epic_order attribute"

        if not include_epic_order or obj.epic_order is None:
            return None

        return obj.epic_order

    def get_epics(self, obj):
        assert hasattr(obj, "epics_attr"), "instance must have a epics_attr attribute"
        return obj.epics_attr

    def get_milestone_slug(self, obj):
        return obj.milestone.slug if obj.milestone else None

    def get_milestone_name(self, obj):
        return obj.milestone.name if obj.milestone else None

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr

    def get_points(self, obj):
        assert hasattr(obj, "role_points_attr"), "instance must have a role_points_attr attribute"
        if obj.role_points_attr is None:
            return {}

        return obj.role_points_attr

    def get_comment(self, obj):
        return ""

    def get_tasks(self, obj):
        include_tasks = getattr(obj, "include_tasks", False)

        if include_tasks:
            assert hasattr(obj, "tasks_attr"), "instance must have a tasks_attr attribute"

        if not include_tasks or obj.tasks_attr is None:
            return []

        return obj.tasks_attr


class UserStorySerializer(UserStoryListSerializer):
    comment = MethodField()
    blocked_note_html = MethodField()
    description = Field()
    description_html = MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class UserStoryNeighborsSerializer(NeighborsSerializerMixin, UserStorySerializer):
    pass


class UserStoryLightSerializer(ProjectExtraInfoSerializerMixin,
                               StatusExtraInfoSerializerMixin,
                               AssignedToExtraInfoSerializerMixin,
                               DueDateSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    milestone = Field(attr="milestone_id")
    project = Field(attr="project_id")
    is_closed = Field()
    created_date = Field()
    modified_date = Field()
    finish_date = Field()
    subject = Field()
    client_requirement = Field()
    team_requirement = Field()
    external_reference = Field()
    version = Field()
    is_blocked = Field()
    blocked_note = Field()


class UserStoryOnlyRefSerializer(serializers.LightSerializer):
    id = Field()
    ref = Field()


class UserStoryNestedSerializer(ProjectExtraInfoSerializerMixin,
                                StatusExtraInfoSerializerMixin,
                                AssignedToExtraInfoSerializerMixin,
                                DueDateSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    milestone = Field(attr="milestone_id")
    project = Field(attr="project_id")
    is_closed = Field()
    created_date = Field()
    modified_date = Field()
    finish_date = Field()
    subject = Field()
    client_requirement = Field()
    team_requirement = Field()
    external_reference = Field()
    version = Field()
    is_blocked = Field()
    blocked_note = Field()
    backlog_order = Field()
    sprint_order = Field()
    kanban_order = Field()

    epics = MethodField()
    points = MethodField()
    total_points = MethodField()

    def get_epics(self, obj):
        assert hasattr(obj, "epics_attr"), "instance must have a epics_attr attribute"
        return obj.epics_attr

    def get_points(self, obj):
        assert hasattr(obj, "role_points_attr"), "instance must have a role_points_attr attribute"
        if obj.role_points_attr is None:
            return {}

        return obj.role_points_attr

    def get_total_points(self, obj):
        assert hasattr(obj, "total_points_attr"), "instance must have a total_points_attr attribute"
        return obj.total_points_attr
