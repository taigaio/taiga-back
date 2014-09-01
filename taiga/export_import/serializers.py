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

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile

from rest_framework import serializers

import json
import base64
import os
import io
from collections import OrderedDict

from taiga.projects import models as projects_models
from taiga.projects.userstories import models as userstories_models
from taiga.projects.tasks import models as tasks_models
from taiga.projects.issues import models as issues_models
from taiga.projects.milestones import models as milestones_models
from taiga.projects.wiki import models as wiki_models
from taiga.projects.votes import models as votes_models
from taiga.projects.notifications import models as notifications_models
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.users import models as users_models
from taiga.projects.votes import services as votes_service
from taiga.projects.history import services as history_service
from taiga.base.serializers import JsonField, PgArrayField

class AttachedFileField(serializers.WritableField):
    read_only = False

    def to_native(self, obj):
        if not obj:
            return None

        return OrderedDict([
            ("data", base64.b64encode(obj.read()).decode('utf-8')),
            ("name", os.path.basename(obj.name)),
        ])

    def from_native(self, data):
        if not data:
            return None
        return ContentFile(base64.b64decode(data['data']), name=data['name'])


class UserRelatedField(serializers.RelatedField):
    read_only = False

    def to_native(self, obj):
        if obj:
            return obj.email
        return None

    def from_native(self, data):
        try:
            return users_models.User.objects.get(email=data)
        except users_models.User.DoesNotExist:
            return None

class ProjectRelatedField(serializers.RelatedField):
    read_only = False

    def __init__(self, slug_field, *args, **kwargs):
        self.slug_field = slug_field
        super().__init__(*args, **kwargs)

    def to_native(self, obj):
        if obj:
            return getattr(obj, self.slug_field)
        return None

    def from_native(self, data):
        try:
            kwargs = {self.slug_field: data, "project": self.context['project']}
            return self.queryset.get(**kwargs)
        except self.parent.opts.model.DoesNotExist:
            return None


class PointsExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Points
        exclude = ('id', 'project')

class UserStoryStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.UserStoryStatus
        exclude = ('id', 'project')

class TaskStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.TaskStatus
        exclude = ('id', 'project')

class IssueStatusExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.IssueStatus
        exclude = ('id', 'project')

class PriorityExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Priority
        exclude = ('id', 'project')

class SeverityExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.Severity
        exclude = ('id', 'project')

class IssueTypeExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = projects_models.IssueType
        exclude = ('id', 'project')

class RoleExportSerializer(serializers.ModelSerializer):
    permissions = PgArrayField(required=False)

    class Meta:
        model = users_models.Role
        exclude = ('id', 'project')

class MembershipExportSerializer(serializers.ModelSerializer):
    user = UserRelatedField(required=False)
    role = ProjectRelatedField(slug_field="slug")

    class Meta:
        model = projects_models.Membership
        exclude = ('id', 'project')

    def full_clean(self, instance):
        return instance


class RolePointsExportSerializer(serializers.ModelSerializer):
    role = ProjectRelatedField(slug_field="slug")
    points = ProjectRelatedField(slug_field="name")

    class Meta:
        model = userstories_models.RolePoints
        exclude = ('id', 'user_story')

class MilestoneExportSerializer(serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    watchers = UserRelatedField(many=True, required=False)
    tasks_without_us = serializers.SerializerMethodField("get_tasks_without_us")

    class Meta:
        model = milestones_models.Milestone
        exclude = ('id', 'project')

    def get_tasks_without_us(self, obj):
        queryset = tasks_models.Task.objects.filter(milestone=obj, user_story__isnull=True)
        return TaskExportSerializer(queryset.order_by('ref'), many=True).data

class AttachmentExportSerializer(serializers.ModelSerializer):
    owner = UserRelatedField()
    attached_file = AttachedFileField()

    class Meta:
        model = attachments_models.Attachment
        exclude = ('id', 'content_type', 'object_id', 'project')

class AttachmentExportSerializerMixin(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField("get_attachments")

    def get_attachments(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        attachments_qs = attachments_models.Attachment.objects.filter(object_id=obj.pk, content_type=content_type)
        return AttachmentExportSerializer(attachments_qs, many=True).data

class TaskExportSerializer(AttachmentExportSerializerMixin, serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name", required=False)
    milestone = ProjectRelatedField(slug_field="slug", required=False)
    assigned_to = UserRelatedField(required=False)
    watchers = UserRelatedField(many=True, required=False)

    class Meta:
        model = tasks_models.Task
        exclude = ('id', 'project', 'user_story')

class UserStoryExportSerializer(AttachmentExportSerializerMixin, serializers.ModelSerializer):
    role_points = RolePointsExportSerializer(many=True, required=False)
    generated_from_issue = ProjectRelatedField(slug_field="ref", required=False)
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name", required=False)
    tasks = TaskExportSerializer(many=True, required=False)
    milestone = ProjectRelatedField(slug_field="slug", required=False)
    watchers = UserRelatedField(many=True, required=False)

    class Meta:
        model = userstories_models.UserStory
        exclude = ('id', 'project', 'points')

def _convert_user(user_pk):
    try:
        user = users_models.User.objects.get(pk=user_pk)
    except users_models.User.DoesNotExist:
        return "#imported#{}".format(user_pk)
    return user.email

def _convert_user_tuple(user_tuple):
    return (_convert_user(user_tuple[0]), user_tuple[1])

class HistoryExportSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField("get_user")
    diff = serializers.SerializerMethodField("get_diff")
    snapshot = JsonField()
    values = serializers.SerializerMethodField("get_values")

    def get_user(self, obj):
        return (_convert_user(obj.user['pk']), obj.user['name'])

    def get_values(self, obj):
        for key, value in obj.values.items():
            if key == "users":
                obj.values["users"] = dict(map(_convert_user_tuple, value.items()))

        return obj.values

    def get_diff(self, obj):
        for key, value in obj.diff.items():
            if key == "assigned_to":
                obj.diff["assigned_to"] = map(_convert_user, value)

        return obj.diff

    class Meta:
        model = history_models.HistoryEntry

class HistoryExportSerializerMixin(serializers.ModelSerializer):
    history = serializers.SerializerMethodField("get_history")

    def get_history(self, obj):
        history_qs = history_service.get_history_queryset_by_model_instance(obj)
        return HistoryExportSerializer(history_qs, many=True).data


class IssueExportSerializer(HistoryExportSerializerMixin, AttachmentExportSerializerMixin, serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name", required=False)
    assigned_to = UserRelatedField(required=False)
    priority = ProjectRelatedField(slug_field="name", required=False)
    severity = ProjectRelatedField(slug_field="name", required=False)
    type = ProjectRelatedField(slug_field="name", required=False)
    milestone = ProjectRelatedField(slug_field="slug", required=False)
    watchers = UserRelatedField(many=True, required=False)
    votes = serializers.SerializerMethodField("get_votes")

    def get_votes(self, obj):
        return [x.email for x in votes_service.get_voters(obj)]

    class Meta:
        model = issues_models.Issue
        exclude = ('id', 'project')

class WikiPageExportSerializer(AttachmentExportSerializerMixin, serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    last_modifier = UserRelatedField(required=False)
    watchers = UserRelatedField(many=True, required=False)

    class Meta:
        model = wiki_models.WikiPage
        exclude = ('id', 'project')

class WikiLinkExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = wiki_models.WikiLink
        exclude = ('id', 'project')

class ProjectExportSerializer(serializers.ModelSerializer):
    owner = UserRelatedField(required=False)
    default_points = serializers.SlugRelatedField(slug_field="name", required=False)
    default_us_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_task_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_priority = serializers.SlugRelatedField(slug_field="name", required=False)
    default_severity = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_type = serializers.SlugRelatedField(slug_field="name", required=False)
    memberships = MembershipExportSerializer(many=True, required=False)
    points = PointsExportSerializer(many=True, required=False)
    us_statuses = UserStoryStatusExportSerializer(many=True, required=False)
    task_statuses = TaskStatusExportSerializer(many=True, required=False)
    issue_statuses = IssueStatusExportSerializer(many=True, required=False)
    priorities = PriorityExportSerializer(many=True, required=False)
    severities = SeverityExportSerializer(many=True, required=False)
    issue_types = IssueTypeExportSerializer(many=True, required=False)
    roles = RoleExportSerializer(many=True, required=False)
    milestones = MilestoneExportSerializer(many=True, required=False)
    wiki_pages = WikiPageExportSerializer(many=True, required=False)
    wiki_links = WikiLinkExportSerializer(many=True, required=False)
    user_stories = UserStoryExportSerializer(many=True, required=False)
    issues = IssueExportSerializer(many=True, required=False)
    tags_colors = JsonField(required=False)
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = projects_models.Project
        exclude = ('id', 'creation_template', 'members')
