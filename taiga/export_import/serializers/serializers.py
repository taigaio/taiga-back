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

import copy

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.fields import JsonField, PgArrayField

from taiga.projects import models as projects_models
from taiga.projects.custom_attributes import models as custom_attributes_models
from taiga.projects.userstories import models as userstories_models
from taiga.projects.tasks import models as tasks_models
from taiga.projects.issues import models as issues_models
from taiga.projects.milestones import models as milestones_models
from taiga.projects.wiki import models as wiki_models
from taiga.projects.history import models as history_models
from taiga.projects.attachments import models as attachments_models
from taiga.timeline import models as timeline_models
from taiga.users import models as users_models
from taiga.projects.votes import services as votes_service

from .fields import (FileField, RelatedNoneSafeField, UserRelatedField,
                     UserPkField, CommentField, ProjectRelatedField,
                     HistoryUserField, HistoryValuesField, HistoryDiffField,
                     TimelineDataField, ContentTypeField)
from .mixins import (HistoryExportSerializerMixin,
                     AttachmentExportSerializerMixin,
                     CustomAttributesValuesExportSerializerMixin,
                     WatcheableObjectModelSerializerMixin)
from .cache import (_custom_tasks_attributes_cache,
                    _custom_userstories_attributes_cache,
                    _custom_issues_attributes_cache)


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


class UserStoryCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.UserStoryCustomAttribute
        exclude = ('id', 'project')


class TaskCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.TaskCustomAttribute
        exclude = ('id', 'project')


class IssueCustomAttributeExportSerializer(serializers.ModelSerializer):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.IssueCustomAttribute
        exclude = ('id', 'project')


class BaseCustomAttributesValuesExportSerializer(serializers.ModelSerializer):
    attributes_values = JsonField(source="attributes_values",required=True)
    _custom_attribute_model = None
    _container_field = None

    class Meta:
        exclude = ("id",)

    def validate_attributes_values(self, attrs, source):
        # values must be a dict
        data_values = attrs.get("attributes_values", None)
        if self.object:
            data_values = (data_values or self.object.attributes_values)

        if type(data_values) is not dict:
            raise ValidationError(_("Invalid content. It must be {\"key\": \"value\",...}"))

        # Values keys must be in the container object project
        data_container = attrs.get(self._container_field, None)
        if data_container:
            project_id = data_container.project_id
        elif self.object:
            project_id = getattr(self.object, self._container_field).project_id
        else:
            project_id = None

        values_ids = list(data_values.keys())
        qs = self._custom_attribute_model.objects.filter(project=project_id,
                                                         id__in=values_ids)
        if qs.count() != len(values_ids):
            raise ValidationError(_("It contain invalid custom fields."))

        return attrs

class UserStoryCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.UserStoryCustomAttribute
    _container_model = "userstories.UserStory"
    _container_field = "user_story"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.UserStoryCustomAttributesValues


class TaskCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.TaskCustomAttribute
    _container_field = "task"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.TaskCustomAttributesValues


class IssueCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    _custom_attribute_model = custom_attributes_models.IssueCustomAttribute
    _container_field = "issue"

    class Meta(BaseCustomAttributesValuesExportSerializer.Meta):
        model = custom_attributes_models.IssueCustomAttributesValues


class MembershipExportSerializer(serializers.ModelSerializer):
    user = UserRelatedField(required=False)
    role = ProjectRelatedField(slug_field="name")
    invited_by = UserRelatedField(required=False)

    class Meta:
        model = projects_models.Membership
        exclude = ('id', 'project', 'token')

    def full_clean(self, instance):
        return instance


class RolePointsExportSerializer(serializers.ModelSerializer):
    role = ProjectRelatedField(slug_field="name")
    points = ProjectRelatedField(slug_field="name")

    class Meta:
        model = userstories_models.RolePoints
        exclude = ('id', 'user_story')


class MilestoneExportSerializer(WatcheableObjectModelSerializerMixin):
    owner = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    estimated_start = serializers.DateField(required=False)
    estimated_finish = serializers.DateField(required=False)

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(MilestoneExportSerializer, self).__init__(*args, **kwargs)
        if project:
            self.project = project

    def validate_name(self, attrs, source):
        """
        Check the milestone name is not duplicated in the project
        """
        name = attrs[source]
        qs = self.project.milestones.filter(name=name)
        if qs.exists():
            raise serializers.ValidationError(_("Name duplicated for the project"))

        return attrs

    class Meta:
        model = milestones_models.Milestone
        exclude = ('id', 'project')


class TaskExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                           AttachmentExportSerializerMixin, WatcheableObjectModelSerializerMixin):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    user_story = ProjectRelatedField(slug_field="ref", required=False)
    milestone = ProjectRelatedField(slug_field="name", required=False)
    assigned_to = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = tasks_models.Task
        exclude = ('id', 'project')

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_tasks_attributes_cache:
            _custom_tasks_attributes_cache[project.id] = list(project.taskcustomattributes.all().values('id', 'name'))
        return _custom_tasks_attributes_cache[project.id]


class UserStoryExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                                AttachmentExportSerializerMixin, WatcheableObjectModelSerializerMixin):
    role_points = RolePointsExportSerializer(many=True, required=False)
    owner = UserRelatedField(required=False)
    assigned_to = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    milestone = ProjectRelatedField(slug_field="name", required=False)
    modified_date = serializers.DateTimeField(required=False)
    generated_from_issue = ProjectRelatedField(slug_field="ref", required=False)

    class Meta:
        model = userstories_models.UserStory
        exclude = ('id', 'project', 'points', 'tasks')

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_userstories_attributes_cache:
            _custom_userstories_attributes_cache[project.id] = list(project.userstorycustomattributes.all().values('id', 'name'))
        return _custom_userstories_attributes_cache[project.id]


class IssueExportSerializer(CustomAttributesValuesExportSerializerMixin, HistoryExportSerializerMixin,
                            AttachmentExportSerializerMixin, WatcheableObjectModelSerializerMixin):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    assigned_to = UserRelatedField(required=False)
    priority = ProjectRelatedField(slug_field="name")
    severity = ProjectRelatedField(slug_field="name")
    type = ProjectRelatedField(slug_field="name")
    milestone = ProjectRelatedField(slug_field="name", required=False)
    votes = serializers.SerializerMethodField("get_votes")
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = issues_models.Issue
        exclude = ('id', 'project')

    def get_votes(self, obj):
        return [x.email for x in votes_service.get_voters(obj)]

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_issues_attributes_cache:
            _custom_issues_attributes_cache[project.id] = list(project.issuecustomattributes.all().values('id', 'name'))
        return _custom_issues_attributes_cache[project.id]


class WikiPageExportSerializer(HistoryExportSerializerMixin, AttachmentExportSerializerMixin,
                               WatcheableObjectModelSerializerMixin):
    owner = UserRelatedField(required=False)
    last_modifier = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = wiki_models.WikiPage
        exclude = ('id', 'project')


class WikiLinkExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = wiki_models.WikiLink
        exclude = ('id', 'project')



class TimelineExportSerializer(serializers.ModelSerializer):
    data = TimelineDataField()
    data_content_type = ContentTypeField()
    class Meta:
        model = timeline_models.Timeline
        exclude = ('id', 'project', 'namespace', 'object_id', 'content_type')


class ProjectExportSerializer(WatcheableObjectModelSerializerMixin):
    logo = FileField(required=False)
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    roles = RoleExportSerializer(many=True, required=False)
    owner = UserRelatedField(required=False)
    memberships = MembershipExportSerializer(many=True, required=False)
    points = PointsExportSerializer(many=True, required=False)
    us_statuses = UserStoryStatusExportSerializer(many=True, required=False)
    task_statuses = TaskStatusExportSerializer(many=True, required=False)
    issue_types = IssueTypeExportSerializer(many=True, required=False)
    issue_statuses = IssueStatusExportSerializer(many=True, required=False)
    priorities = PriorityExportSerializer(many=True, required=False)
    severities = SeverityExportSerializer(many=True, required=False)
    tags_colors = JsonField(required=False)
    default_points = serializers.SlugRelatedField(slug_field="name", required=False)
    default_us_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_task_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_priority = serializers.SlugRelatedField(slug_field="name", required=False)
    default_severity = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_type = serializers.SlugRelatedField(slug_field="name", required=False)
    userstorycustomattributes = UserStoryCustomAttributeExportSerializer(many=True, required=False)
    taskcustomattributes = TaskCustomAttributeExportSerializer(many=True, required=False)
    issuecustomattributes = IssueCustomAttributeExportSerializer(many=True, required=False)
    user_stories = UserStoryExportSerializer(many=True, required=False)
    tasks = TaskExportSerializer(many=True, required=False)
    milestones = MilestoneExportSerializer(many=True, required=False)
    issues = IssueExportSerializer(many=True, required=False)
    wiki_links = WikiLinkExportSerializer(many=True, required=False)
    wiki_pages = WikiPageExportSerializer(many=True, required=False)

    class Meta:
        model = projects_models.Project
        exclude = ('id', 'creation_template', 'members')
