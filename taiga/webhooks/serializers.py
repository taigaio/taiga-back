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
from taiga.base.fields import TagsField, PgArrayField, JsonField

from taiga.front.templatetags.functions import resolve as resolve_front_url

from taiga.projects.history import models as history_models
from taiga.projects.issues import models as issue_models
from taiga.projects.milestones import models as milestone_models
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer
from taiga.projects.services import get_logo_big_thumbnail_url
from taiga.projects.tasks import models as task_models
from taiga.projects.userstories import models as us_models
from taiga.projects.wiki import models as wiki_models

from taiga.users.gravatar import get_gravatar_url
from taiga.users.services import get_photo_or_gravatar_url

from .models import Webhook, WebhookLog


########################################################################
## WebHooks
########################################################################

class WebhookSerializer(serializers.ModelSerializer):
    logs_counter = serializers.SerializerMethodField("get_logs_counter")

    class Meta:
        model = Webhook

    def get_logs_counter(self, obj):
        return obj.logs.count()


class WebhookLogSerializer(serializers.ModelSerializer):
    request_data = JsonField()
    request_headers = JsonField()
    response_headers = JsonField()

    class Meta:
        model = WebhookLog


########################################################################
## User
########################################################################

class UserSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    permalink = serializers.SerializerMethodField("get_permalink")
    gravatar_url = serializers.SerializerMethodField("get_gravatar_url")
    username = serializers.SerializerMethodField("get_username")
    full_name = serializers.SerializerMethodField("get_full_name")
    photo = serializers.SerializerMethodField("get_photo")

    def get_pk(self, obj):
        return obj.pk

    def get_permalink(self, obj):
        return resolve_front_url("user", obj.username)

    def get_gravatar_url(self, obj):
        return get_gravatar_url(obj.email)

    def get_username(self, obj):
        return obj.get_username

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_photo(self, obj):
        return get_photo_or_gravatar_url(obj)

########################################################################
## Project
########################################################################

class ProjectSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    permalink = serializers.SerializerMethodField("get_permalink")
    name = serializers.SerializerMethodField("get_name")
    logo_big_url = serializers.SerializerMethodField("get_logo_big_url")

    def get_pk(self, obj):
        return obj.pk

    def get_permalink(self, obj):
        return resolve_front_url("project", obj.slug)

    def get_name(self, obj):
        return obj.name

    def get_logo_big_url(self, obj):
        return get_logo_big_thumbnail_url(obj)


########################################################################
## History Serializer
########################################################################

class HistoryDiffField(serializers.Field):
    def to_native(self, value):
        # Tip: 'value' is the object returned by
        #      taiga.projects.history.models.HistoryEntry.values_diff()

        ret = {}

        for key, val in value.items():
            if key in ["attachments", "custom_attributes"]:
                ret[key] = val
            elif key == "points":
                ret[key] = {k: {"from": v[0], "to": v[1]} for k, v in val.items()}
            else:
                ret[key] = {"from": val[0], "to": val[1]}

        return ret


class HistoryEntrySerializer(serializers.ModelSerializer):
    diff = HistoryDiffField(source="values_diff")

    class Meta:
        model = history_models.HistoryEntry
        exclude = ("id", "type", "key", "is_hidden", "is_snapshot", "snapshot", "user", "delete_comment_user",
                   "values", "created_at")


########################################################################
## _Misc_
########################################################################

class CustomAttributesValuesWebhookSerializerMixin(serializers.ModelSerializer):
    custom_attributes_values = serializers.SerializerMethodField("get_custom_attributes_values")

    def custom_attributes_queryset(self, project):
        raise NotImplementedError()

    def get_custom_attributes_values(self, obj):
        def _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values):
            ret = {}
            for attr in custom_attributes:
                value = values.get(str(attr["id"]), None)
                if value is not  None:
                    ret[attr["name"]] = value

            return ret

        try:
            values =  obj.custom_attributes_values.attributes_values
            custom_attributes = self.custom_attributes_queryset(obj.project).values('id', 'name')

            return _use_name_instead_id_as_key_in_custom_attributes_values(custom_attributes, values)
        except ObjectDoesNotExist:
            return None


class RolePointsSerializer(serializers.Serializer):
    role = serializers.SerializerMethodField("get_role")
    name = serializers.SerializerMethodField("get_name")
    value = serializers.SerializerMethodField("get_value")

    def get_role(self, obj):
        return obj.role.name

    def get_name(self, obj):
        return obj.points.name

    def get_value(self, obj):
        return obj.points.value


class UserStoryStatusSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    slug = serializers.SerializerMethodField("get_slug")
    color = serializers.SerializerMethodField("get_color")
    is_closed = serializers.SerializerMethodField("get_is_closed")
    is_archived = serializers.SerializerMethodField("get_is_archived")

    def get_pk(self, obj):
        return obj.pk

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


class TaskStatusSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    slug = serializers.SerializerMethodField("get_slug")
    color = serializers.SerializerMethodField("get_color")
    is_closed = serializers.SerializerMethodField("get_is_closed")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed


class IssueStatusSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    slug = serializers.SerializerMethodField("get_slug")
    color = serializers.SerializerMethodField("get_color")
    is_closed = serializers.SerializerMethodField("get_is_closed")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_slug(self, obj):
        return obj.slug

    def get_color(self, obj):
        return obj.color

    def get_is_closed(self, obj):
        return obj.is_closed


class IssueTypeSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    color = serializers.SerializerMethodField("get_color")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


class PrioritySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    color = serializers.SerializerMethodField("get_color")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


class SeveritySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    color = serializers.SerializerMethodField("get_color")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_color(self, obj):
        return obj.color


########################################################################
## Milestone
########################################################################

class MilestoneSerializer(serializers.ModelSerializer):
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()

    class Meta:
        model = milestone_models.Milestone
        exclude = ("order", "watchers")

    def get_permalink(self, obj):
        return resolve_front_url("taskboard", obj.project.slug, obj.slug)


########################################################################
## User Story
########################################################################

class UserStorySerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                          serializers.ModelSerializer):
    permalink = serializers.SerializerMethodField("get_permalink")
    tags = TagsField(default=[], required=False)
    external_reference = PgArrayField(required=False)
    project = ProjectSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    points = RolePointsSerializer(source="role_points", many=True)
    status = UserStoryStatusSerializer()
    milestone = MilestoneSerializer()

    class Meta:
        model = us_models.UserStory
        exclude = ("backlog_order", "sprint_order", "kanban_order", "version", "total_watchers", "is_watcher")

    def get_permalink(self, obj):
        return resolve_front_url("userstory", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.userstorycustomattributes.all()


########################################################################
## Task
########################################################################

class TaskSerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                     serializers.ModelSerializer):
    permalink = serializers.SerializerMethodField("get_permalink")
    tags = TagsField(default=[], required=False)
    project = ProjectSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    status = TaskStatusSerializer()
    user_story = UserStorySerializer()
    milestone = MilestoneSerializer()

    class Meta:
        model = task_models.Task
        exclude = ("version", "total_watchers", "is_watcher")

    def get_permalink(self, obj):
        return resolve_front_url("task", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.taskcustomattributes.all()


########################################################################
## Issue
########################################################################

class IssueSerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                      serializers.ModelSerializer):
    permalink = serializers.SerializerMethodField("get_permalink")
    tags = TagsField(default=[], required=False)
    project = ProjectSerializer()
    milestone = MilestoneSerializer()
    owner = UserSerializer()
    assigned_to = UserSerializer()
    status = IssueStatusSerializer()
    type = IssueTypeSerializer()
    priority = PrioritySerializer()
    severity = SeveritySerializer()

    class Meta:
        model = issue_models.Issue
        exclude = ("version", "total_watchers", "is_watcher")

    def get_permalink(self, obj):
        return resolve_front_url("issue", obj.project.slug, obj.ref)

    def custom_attributes_queryset(self, project):
        return project.issuecustomattributes.all()


########################################################################
## Wiki Page
########################################################################

class WikiPageSerializer(serializers.ModelSerializer):
    permalink = serializers.SerializerMethodField("get_permalink")
    project = ProjectSerializer()
    owner = UserSerializer()
    last_modifier = UserSerializer()

    class Meta:
        model = wiki_models.WikiPage
        exclude = ("watchers", "total_watchers", "is_watcher", "version")

    def get_permalink(self, obj):
        return resolve_front_url("wiki", obj.project.slug, obj.slug)
