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

from django.core.exceptions import ObjectDoesNotExist

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.front.templatetags.functions import resolve as resolve_front_url

from taiga.projects.services import get_logo_big_thumbnail_url

from taiga.users.services import get_user_photo_url
from taiga.users.gravatar import get_user_gravatar_id

########################################################################
# WebHooks
########################################################################


class WebhookSerializer(serializers.LightSerializer):
    id = Field()
    project = Field(attr="project_id")
    name = Field()
    url = Field()
    key = Field()
    logs_counter = MethodField()

    def get_logs_counter(self, obj):
        return obj.logs.count()


class WebhookLogSerializer(serializers.LightSerializer):
    id = Field()
    webhook = Field(attr="webhook_id")
    url = Field()
    status = Field()
    request_data = Field()
    request_headers = Field()
    response_data = Field()
    response_headers = Field()
    duration = Field()
    created = Field()


########################################################################
# User
########################################################################

class UserSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    permalink = MethodField()
    username = MethodField()
    full_name = MethodField()
    photo = MethodField()
    gravatar_id = MethodField()

    def get_permalink(self, obj):
        return resolve_front_url("user", obj.username)

    def get_username(self, obj):
        return obj.get_username()

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_photo(self, obj):
        return get_user_photo_url(obj)

    def get_gravatar_id(self, obj):
        return get_user_gravatar_id(obj)

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


########################################################################
# Project
########################################################################

class ProjectSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    permalink = MethodField()
    name = MethodField()
    logo_big_url = MethodField()

    def get_permalink(self, obj):
        return resolve_front_url("project", obj.slug)

    def get_name(self, obj):
        return obj.name

    def get_logo_big_url(self, obj):
        return get_logo_big_thumbnail_url(obj)


########################################################################
# History Serializer
########################################################################

class HistoryDiffField(Field):
    def to_value(self, value):
        # Tip: 'value' is the object returned by
        #      taiga.projects.history.models.HistoryEntry.values_diff()

        ret = {}
        for key, val in value.items():
            if key in ["attachments", "custom_attributes", "description_diff"]:
                ret[key] = val
            elif key == "points":
                ret[key] = {k: {"from": v[0], "to": v[1]} for k, v in val.items()}
            else:
                ret[key] = {"from": val[0], "to": val[1]}

        return ret


class HistoryEntrySerializer(serializers.LightSerializer):
    comment = Field()
    comment_html = Field()
    delete_comment_date = Field()
    comment_versions = Field()
    edit_comment_date = Field()
    diff = HistoryDiffField(attr="values_diff")


########################################################################
# _Misc_
########################################################################

class CustomAttributesValuesWebhookSerializerMixin(serializers.LightSerializer):
    custom_attributes_values = MethodField()

    def custom_attributes_queryset(self, project):
        raise NotImplementedError()

    def get_custom_attributes_values(self, obj):
        def _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values):
            ret = {}
            for attr in custom_attributes:
                value = values.get(str(attr["id"]), None)
                if value is not None:
                    ret[attr["name"]] = value

            return ret

        try:
            values = obj.custom_attributes_values.attributes_values
            custom_attributes = self.custom_attributes_queryset(obj.project).values('id', 'name')

            return _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values)
        except ObjectDoesNotExist:
            return None


class RolePointsSerializer(serializers.LightSerializer):
    role = MethodField()
    name = MethodField()
    value = MethodField()

    def get_role(self, obj):
        return obj.role.name

    def get_name(self, obj):
        return obj.points.name

    def get_value(self, obj):
        return obj.points.value


class EpicStatusSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    slug = MethodField()
    color = MethodField()
    is_closed = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed


class UserStoryStatusSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    slug = MethodField()
    color = MethodField()
    is_closed = MethodField()
    is_archived = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed

    def get_is_archived(self, obj):
        return obj.is_archived


class TaskStatusSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    slug = MethodField()
    color = MethodField()
    is_closed = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed


class IssueStatusSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    slug = MethodField()
    color = MethodField()
    is_closed = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed


class IssueTypeSerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    color = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


class PrioritySerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    color = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


class SeveritySerializer(serializers.LightSerializer):
    id = Field(attr="pk")
    name = MethodField()
    color = MethodField()

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


########################################################################
# Milestone
########################################################################

class MilestoneSerializer(serializers.LightSerializer):
    id = Field()
    name = Field()
    slug = Field()
    estimated_start = Field()
    estimated_finish = Field()
    created_date = Field()
    modified_date = Field()
    closed = Field()
    disponibility = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()

    def get_permalink(self, obj):
        return resolve_front_url("taskboard", obj.project.slug, obj.slug)

    def to_value(self, instance):
        if instance is None:
            return None

        return super().to_value(instance)


########################################################################
# User Story
########################################################################

class UserStorySerializer(CustomAttributesValuesWebhookSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    project = ProjectSerializer()
    is_closed = Field()
    created_date = Field()
    modified_date = Field()
    finish_date = Field()
    subject = Field()
    client_requirement = Field()
    team_requirement = Field()
    generated_from_issue = Field(attr="generated_from_issue_id")
    external_reference = Field()
    tribe_gig = Field()
    watchers = MethodField()
    is_blocked = Field()
    blocked_note = Field()
    description = Field()
    tags = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    owner = UserSerializer()
    assigned_to = UserSerializer()
    points = MethodField()
    status = UserStoryStatusSerializer()
    milestone = MilestoneSerializer()

    def get_permalink(self, obj):
        return resolve_front_url("userstory", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.userstorycustomattributes.all()

    def get_watchers(self, obj):
        return list(obj.get_watchers().values_list("id", flat=True))

    def get_points(self, obj):
        return RolePointsSerializer(obj.role_points.all(), many=True).data


########################################################################
# Task
########################################################################

class TaskSerializer(CustomAttributesValuesWebhookSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    created_date = Field()
    modified_date = Field()
    finished_date = Field()
    subject = Field()
    us_order = Field()
    taskboard_order = Field()
    is_iocaine = Field()
    external_reference = Field()
    watchers = MethodField()
    is_blocked = Field()
    blocked_note = Field()
    description = Field()
    tags = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    status = TaskStatusSerializer()
    user_story = UserStorySerializer()
    milestone = MilestoneSerializer()

    def get_permalink(self, obj):
        return resolve_front_url("task", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.taskcustomattributes.all()

    def get_watchers(self, obj):
        return list(obj.get_watchers().values_list("id", flat=True))


########################################################################
# Issue
########################################################################

class IssueSerializer(CustomAttributesValuesWebhookSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    created_date = Field()
    modified_date = Field()
    finished_date = Field()
    subject = Field()
    external_reference = Field()
    watchers = MethodField()
    description = Field()
    tags = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    milestone = MilestoneSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    status = IssueStatusSerializer()
    type = IssueTypeSerializer()
    priority = PrioritySerializer()
    severity = SeveritySerializer()

    def get_permalink(self, obj):
        return resolve_front_url("issue", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.issuecustomattributes.all()

    def get_watchers(self, obj):
        return list(obj.get_watchers().values_list("id", flat=True))


########################################################################
# Wiki Page
########################################################################

class WikiPageSerializer(serializers.LightSerializer):
    id = Field()
    slug = Field()
    content = Field()
    created_date = Field()
    modified_date = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()
    last_modifier = UserSerializer()

    def get_permalink(self, obj):
        return resolve_front_url("wiki", obj.project.slug, obj.slug)


########################################################################
# Epic
########################################################################

class EpicSerializer(CustomAttributesValuesWebhookSerializerMixin, serializers.LightSerializer):
    id = Field()
    ref = Field()
    created_date = Field()
    modified_date = Field()
    subject = Field()
    watchers = MethodField()
    description = Field()
    tags = Field()
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    status = EpicStatusSerializer()
    epics_order = Field()
    color = Field()
    client_requirement = Field()
    team_requirement = Field()
    client_requirement = Field()
    team_requirement = Field()

    def get_permalink(self, obj):
        return resolve_front_url("epic", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.epiccustomattributes.all()

    def get_watchers(self, obj):
        return list(obj.get_watchers().values_list("id", flat=True))


class EpicRelatedUserStorySerializer(serializers.LightSerializer):
    id = Field()
    user_story = MethodField()
    epic = MethodField()
    order = Field()

    def get_user_story(self, obj):
        return UserStorySerializer(obj.user_story).data

    def get_epic(self, obj):
        return EpicSerializer(obj.epic).data
