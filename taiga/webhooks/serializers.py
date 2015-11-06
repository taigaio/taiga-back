# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
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

from taiga.projects.userstories import models as us_models
from taiga.projects.tasks import models as task_models
from taiga.projects.issues import models as issue_models
from taiga.projects.milestones import models as milestone_models
from taiga.projects.wiki import models as wiki_models
from taiga.projects.history import models as history_models
from taiga.projects.notifications.mixins import EditableWatchedResourceModelSerializer

from .models import Webhook, WebhookLog


class HistoryDiffField(serializers.Field):
    def to_native(self, obj):
        return {key: {"from": value[0], "to": value[1]} for key, value in obj.items()}


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


class UserSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.full_name


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

class PointSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField("get_pk")
    name = serializers.SerializerMethodField("get_name")
    value = serializers.SerializerMethodField("get_value")

    def get_pk(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.name

    def get_value(self, obj):
        return obj.value


class UserStorySerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                          serializers.ModelSerializer):
    tags = TagsField(default=[], required=False)
    external_reference = PgArrayField(required=False)
    owner = UserSerializer()
    assigned_to = UserSerializer()
    points = PointSerializer(many=True)

    class Meta:
        model = us_models.UserStory
        exclude = ("backlog_order", "sprint_order", "kanban_order", "version")

    def custom_attributes_queryset(self, project):
        return project.userstorycustomattributes.all()


class TaskSerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                     serializers.ModelSerializer):
    tags = TagsField(default=[], required=False)
    owner = UserSerializer()
    assigned_to = UserSerializer()

    class Meta:
        model = task_models.Task

    def custom_attributes_queryset(self, project):
        return project.taskcustomattributes.all()


class IssueSerializer(CustomAttributesValuesWebhookSerializerMixin, EditableWatchedResourceModelSerializer,
                      serializers.ModelSerializer):
    tags = TagsField(default=[], required=False)
    owner = UserSerializer()
    assigned_to = UserSerializer()

    class Meta:
        model = issue_models.Issue

    def custom_attributes_queryset(self, project):
        return project.issuecustomattributes.all()


class WikiPageSerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    last_modifier = UserSerializer()

    class Meta:
        model = wiki_models.WikiPage
        exclude = ("watchers", "version")


class MilestoneSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = milestone_models.Milestone
        exclude = ("order", "watchers")


class HistoryEntrySerializer(serializers.ModelSerializer):
    diff = HistoryDiffField()
    snapshot = JsonField()
    values = JsonField()
    user = JsonField()
    delete_comment_user = JsonField()

    class Meta:
        model = history_models.HistoryEntry
