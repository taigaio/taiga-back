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

from django.utils.translation import ugettext as _

from taiga.base.api import serializers
from taiga.base.api import validators
from taiga.base.fields import JsonField, PgArrayField
from taiga.base.exceptions import ValidationError

from taiga.projects import models as projects_models
from taiga.projects.custom_attributes import models as custom_attributes_models
from taiga.projects.epics import models as epics_models
from taiga.projects.userstories import models as userstories_models
from taiga.projects.tasks import models as tasks_models
from taiga.projects.issues import models as issues_models
from taiga.projects.milestones import models as milestones_models
from taiga.projects.wiki import models as wiki_models
from taiga.timeline import models as timeline_models
from taiga.users import models as users_models

from .fields import (FileField, UserRelatedField,
                     ProjectRelatedField,
                     TimelineDataField, ContentTypeField)
from .mixins import WatcheableObjectModelValidatorMixin
from .cache import (_custom_tasks_attributes_cache,
                    _custom_epics_attributes_cache,
                    _custom_userstories_attributes_cache,
                    _custom_issues_attributes_cache)


class PointsExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.Points
        exclude = ('id', 'project')


class EpicStatusExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.EpicStatus
        exclude = ('id', 'project')


class UserStoryStatusExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.UserStoryStatus
        exclude = ('id', 'project')


class TaskStatusExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.TaskStatus
        exclude = ('id', 'project')


class IssueStatusExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.IssueStatus
        exclude = ('id', 'project')


class PriorityExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.Priority
        exclude = ('id', 'project')


class SeverityExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.Severity
        exclude = ('id', 'project')


class IssueTypeExportValidator(validators.ModelValidator):
    class Meta:
        model = projects_models.IssueType
        exclude = ('id', 'project')


class RoleExportValidator(validators.ModelValidator):
    permissions = PgArrayField(required=False)

    class Meta:
        model = users_models.Role
        exclude = ('id', 'project')


class EpicCustomAttributeExportValidator(validators.ModelValidator):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.EpicCustomAttribute
        exclude = ('id', 'project')


class UserStoryCustomAttributeExportValidator(validators.ModelValidator):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.UserStoryCustomAttribute
        exclude = ('id', 'project')


class TaskCustomAttributeExportValidator(validators.ModelValidator):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.TaskCustomAttribute
        exclude = ('id', 'project')


class IssueCustomAttributeExportValidator(validators.ModelValidator):
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = custom_attributes_models.IssueCustomAttribute
        exclude = ('id', 'project')


class BaseCustomAttributesValuesExportValidator(validators.ModelValidator):
    attributes_values = JsonField(source="attributes_values", required=True)
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


class EpicCustomAttributesValuesExportValidator(BaseCustomAttributesValuesExportValidator):
    _custom_attribute_model = custom_attributes_models.EpicCustomAttribute
    _container_model = "epics.Epic"
    _container_field = "epic"

    class Meta(BaseCustomAttributesValuesExportValidator.Meta):
        model = custom_attributes_models.EpicCustomAttributesValues


class UserStoryCustomAttributesValuesExportValidator(BaseCustomAttributesValuesExportValidator):
    _custom_attribute_model = custom_attributes_models.UserStoryCustomAttribute
    _container_model = "userstories.UserStory"
    _container_field = "user_story"

    class Meta(BaseCustomAttributesValuesExportValidator.Meta):
        model = custom_attributes_models.UserStoryCustomAttributesValues


class TaskCustomAttributesValuesExportValidator(BaseCustomAttributesValuesExportValidator):
    _custom_attribute_model = custom_attributes_models.TaskCustomAttribute
    _container_field = "task"

    class Meta(BaseCustomAttributesValuesExportValidator.Meta):
        model = custom_attributes_models.TaskCustomAttributesValues


class IssueCustomAttributesValuesExportValidator(BaseCustomAttributesValuesExportValidator):
    _custom_attribute_model = custom_attributes_models.IssueCustomAttribute
    _container_field = "issue"

    class Meta(BaseCustomAttributesValuesExportValidator.Meta):
        model = custom_attributes_models.IssueCustomAttributesValues


class MembershipExportValidator(validators.ModelValidator):
    user = UserRelatedField(required=False)
    role = ProjectRelatedField(slug_field="name")
    invited_by = UserRelatedField(required=False)

    class Meta:
        model = projects_models.Membership
        exclude = ('id', 'project', 'token')

    def full_clean(self, instance):
        return instance


class RolePointsExportValidator(validators.ModelValidator):
    role = ProjectRelatedField(slug_field="name")
    points = ProjectRelatedField(slug_field="name")

    class Meta:
        model = userstories_models.RolePoints
        exclude = ('id', 'user_story')


class MilestoneExportValidator(WatcheableObjectModelValidatorMixin):
    owner = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    estimated_start = serializers.DateField(required=False)
    estimated_finish = serializers.DateField(required=False)

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super(MilestoneExportValidator, self).__init__(*args, **kwargs)
        if project:
            self.project = project

    def validate_name(self, attrs, source):
        """
        Check the milestone name is not duplicated in the project
        """
        name = attrs[source]
        qs = self.project.milestones.filter(name=name)
        if qs.exists():
            raise ValidationError(_("Name duplicated for the project"))

        return attrs

    class Meta:
        model = milestones_models.Milestone
        exclude = ('id', 'project')


class TaskExportValidator(WatcheableObjectModelValidatorMixin):
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


class EpicRelatedUserStoryExportValidator(validators.ModelValidator):
    user_story = ProjectRelatedField(slug_field="ref")
    order = serializers.IntegerField()

    class Meta:
        model = epics_models.RelatedUserStory
        exclude = ('id', 'epic')


class EpicExportValidator(WatcheableObjectModelValidatorMixin):
    owner = UserRelatedField(required=False)
    assigned_to = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    modified_date = serializers.DateTimeField(required=False)
    user_stories = EpicRelatedUserStoryExportValidator(many=True, required=False)

    class Meta:
        model = epics_models.Epic
        exclude = ('id', 'project')

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_epics_attributes_cache:
            _custom_epics_attributes_cache[project.id] = list(
                project.epiccustomattributes.all().values('id', 'name')
            )
        return _custom_epics_attributes_cache[project.id]


class UserStoryExportValidator(WatcheableObjectModelValidatorMixin):
    role_points = RolePointsExportValidator(many=True, required=False)
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
            _custom_userstories_attributes_cache[project.id] = list(
                project.userstorycustomattributes.all().values('id', 'name')
            )
        return _custom_userstories_attributes_cache[project.id]


class IssueExportValidator(WatcheableObjectModelValidatorMixin):
    owner = UserRelatedField(required=False)
    status = ProjectRelatedField(slug_field="name")
    assigned_to = UserRelatedField(required=False)
    priority = ProjectRelatedField(slug_field="name")
    severity = ProjectRelatedField(slug_field="name")
    type = ProjectRelatedField(slug_field="name")
    milestone = ProjectRelatedField(slug_field="name", required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = issues_models.Issue
        exclude = ('id', 'project')

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_issues_attributes_cache:
            _custom_issues_attributes_cache[project.id] = list(project.issuecustomattributes.all().values('id', 'name'))
        return _custom_issues_attributes_cache[project.id]


class WikiPageExportValidator(WatcheableObjectModelValidatorMixin):
    owner = UserRelatedField(required=False)
    last_modifier = UserRelatedField(required=False)
    modified_date = serializers.DateTimeField(required=False)

    class Meta:
        model = wiki_models.WikiPage
        exclude = ('id', 'project')


class WikiLinkExportValidator(validators.ModelValidator):
    class Meta:
        model = wiki_models.WikiLink
        exclude = ('id', 'project')


class TimelineExportValidator(validators.ModelValidator):
    data = TimelineDataField()
    data_content_type = ContentTypeField()

    class Meta:
        model = timeline_models.Timeline
        exclude = ('id', 'project', 'namespace', 'object_id', 'content_type')


class ProjectExportValidator(WatcheableObjectModelValidatorMixin):
    logo = FileField(required=False)
    anon_permissions = PgArrayField(required=False)
    public_permissions = PgArrayField(required=False)
    modified_date = serializers.DateTimeField(required=False)
    roles = RoleExportValidator(many=True, required=False)
    owner = UserRelatedField(required=False)
    memberships = MembershipExportValidator(many=True, required=False)
    points = PointsExportValidator(many=True, required=False)
    us_statuses = UserStoryStatusExportValidator(many=True, required=False)
    task_statuses = TaskStatusExportValidator(many=True, required=False)
    issue_types = IssueTypeExportValidator(many=True, required=False)
    issue_statuses = IssueStatusExportValidator(many=True, required=False)
    priorities = PriorityExportValidator(many=True, required=False)
    severities = SeverityExportValidator(many=True, required=False)
    tags_colors = JsonField(required=False)
    creation_template = serializers.SlugRelatedField(slug_field="slug", required=False)
    default_points = serializers.SlugRelatedField(slug_field="name", required=False)
    default_us_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_task_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_priority = serializers.SlugRelatedField(slug_field="name", required=False)
    default_severity = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_status = serializers.SlugRelatedField(slug_field="name", required=False)
    default_issue_type = serializers.SlugRelatedField(slug_field="name", required=False)
    userstorycustomattributes = UserStoryCustomAttributeExportValidator(many=True, required=False)
    taskcustomattributes = TaskCustomAttributeExportValidator(many=True, required=False)
    issuecustomattributes = IssueCustomAttributeExportValidator(many=True, required=False)
    user_stories = UserStoryExportValidator(many=True, required=False)
    tasks = TaskExportValidator(many=True, required=False)
    milestones = MilestoneExportValidator(many=True, required=False)
    issues = IssueExportValidator(many=True, required=False)
    wiki_links = WikiLinkExportValidator(many=True, required=False)
    wiki_pages = WikiPageExportValidator(many=True, required=False)

    class Meta:
        model = projects_models.Project
        exclude = ('id', 'members')
