# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field, DateTimeField, MethodField

from taiga.projects.votes import services as votes_service

from .fields import (FileField, UserRelatedField, TimelineDataField,
                     ContentTypeField, SlugRelatedField)
from .mixins import (HistoryExportSerializerMixin,
                     AttachmentExportSerializerMixin,
                     CustomAttributesValuesExportSerializerMixin,
                     WatcheableObjectLightSerializerMixin)
from .cache import (_custom_tasks_attributes_cache,
                    _custom_userstories_attributes_cache,
                    _custom_epics_attributes_cache,
                    _custom_issues_attributes_cache,
                    _tasks_statuses_cache,
                    _issues_statuses_cache,
                    _userstories_statuses_cache,
                    _epics_statuses_cache)


class RelatedExportSerializer(serializers.LightSerializer):
    def to_value(self, value):
        if hasattr(value, 'all'):
            return super().to_value(value.all())
        return super().to_value(value)


class PointsExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    value = Field()


class UserStoryStatusExportSerializer(RelatedExportSerializer):
    name = Field()
    slug = Field()
    order = Field()
    is_closed = Field()
    is_archived = Field()
    color = Field()
    wip_limit = Field()


class UserStoryDueDateExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    by_default = Field()
    color = Field()
    days_to_due = Field()


class EpicStatusExportSerializer(RelatedExportSerializer):
    name = Field()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()


class TaskStatusExportSerializer(RelatedExportSerializer):
    name = Field()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()


class TaskDueDateExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    by_default = Field()
    color = Field()
    days_to_due = Field()


class IssueStatusExportSerializer(RelatedExportSerializer):
    name = Field()
    slug = Field()
    order = Field()
    is_closed = Field()
    color = Field()


class IssueDueDateExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    by_default = Field()
    color = Field()
    days_to_due = Field()


class PriorityExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    color = Field()


class SeverityExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    color = Field()


class IssueTypeExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    color = Field()


class SwimlaneUserStoryStatusExportSerializer(RelatedExportSerializer):
    status = SlugRelatedField(slug_field="name")
    wip_limit = Field()


class SwimlaneExportSerializer(RelatedExportSerializer):
    name = Field()
    order = Field()
    statuses = SwimlaneUserStoryStatusExportSerializer(many=True)


class RoleExportSerializer(RelatedExportSerializer):
    name = Field()
    slug = Field()
    order = Field()
    computable = Field()
    permissions = Field()


class EpicCustomAttributesExportSerializer(RelatedExportSerializer):
    name = Field()
    description = Field()
    type = Field()
    order = Field()
    created_date = DateTimeField()
    modified_date = DateTimeField()


class UserStoryCustomAttributeExportSerializer(RelatedExportSerializer):
    name = Field()
    description = Field()
    type = Field()
    order = Field()
    created_date = DateTimeField()
    modified_date = DateTimeField()


class TaskCustomAttributeExportSerializer(RelatedExportSerializer):
    name = Field()
    description = Field()
    type = Field()
    order = Field()
    created_date = DateTimeField()
    modified_date = DateTimeField()


class IssueCustomAttributeExportSerializer(RelatedExportSerializer):
    name = Field()
    description = Field()
    type = Field()
    order = Field()
    created_date = DateTimeField()
    modified_date = DateTimeField()


class BaseCustomAttributesValuesExportSerializer(RelatedExportSerializer):
    attributes_values = Field(required=True)


class UserStoryCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    user_story = Field(attr="user_story.id")


class TaskCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    task = Field(attr="task.id")


class IssueCustomAttributesValuesExportSerializer(BaseCustomAttributesValuesExportSerializer):
    issue = Field(attr="issue.id")


class MembershipExportSerializer(RelatedExportSerializer):
    user = UserRelatedField()
    role = SlugRelatedField(slug_field="name")
    invited_by = UserRelatedField()
    is_admin = Field()
    email = Field()
    created_at = DateTimeField()
    invitation_extra_text = Field()
    user_order = Field()


class RolePointsExportSerializer(RelatedExportSerializer):
    role = SlugRelatedField(slug_field="name")
    points = SlugRelatedField(slug_field="name")


class MilestoneExportSerializer(WatcheableObjectLightSerializerMixin, RelatedExportSerializer):
    name = Field()
    owner = UserRelatedField()
    created_date = DateTimeField()
    modified_date = DateTimeField()
    estimated_start = Field()
    estimated_finish = Field()
    slug = Field()
    closed = Field()
    disponibility = Field()
    order = Field()


class TaskExportSerializer(CustomAttributesValuesExportSerializerMixin,
                           HistoryExportSerializerMixin,
                           AttachmentExportSerializerMixin,
                           WatcheableObjectLightSerializerMixin,
                           RelatedExportSerializer):
    owner = UserRelatedField()
    status = SlugRelatedField(slug_field="name")
    user_story = SlugRelatedField(slug_field="ref")
    milestone = SlugRelatedField(slug_field="name")
    assigned_to = UserRelatedField()
    modified_date = DateTimeField()
    created_date = DateTimeField()
    finished_date = DateTimeField()
    ref = Field()
    subject = Field()
    us_order = Field()
    taskboard_order = Field()
    description = Field()
    is_iocaine = Field()
    external_reference = Field()
    version = Field()
    blocked_note = Field()
    is_blocked = Field()
    tags = Field()
    due_date = DateTimeField()
    due_date_reason = Field()

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_tasks_attributes_cache:
            _custom_tasks_attributes_cache[project.id] = list(project.taskcustomattributes.all().values('id', 'name'))
        return _custom_tasks_attributes_cache[project.id]

    def statuses_queryset(self, project):
        if project.id not in _tasks_statuses_cache:
            _tasks_statuses_cache[project.id] = {s.id: s.name for s in project.task_statuses.all()}
        return _tasks_statuses_cache[project.id]


class UserStoryExportSerializer(CustomAttributesValuesExportSerializerMixin,
                                HistoryExportSerializerMixin,
                                AttachmentExportSerializerMixin,
                                WatcheableObjectLightSerializerMixin,
                                RelatedExportSerializer):
    role_points = RolePointsExportSerializer(many=True)
    owner = UserRelatedField()
    assigned_to = UserRelatedField()
    assigned_users = MethodField()
    status = SlugRelatedField(slug_field="name")
    swimlane = SlugRelatedField(slug_field="name")
    milestone = SlugRelatedField(slug_field="name")
    modified_date = DateTimeField()
    created_date = DateTimeField()
    finish_date = DateTimeField()
    generated_from_issue = SlugRelatedField(slug_field="ref")
    generated_from_task = SlugRelatedField(slug_field="ref")
    from_task_ref = Field()
    ref = Field()
    is_closed = Field()
    backlog_order = Field()
    sprint_order = Field()
    kanban_order = Field()
    subject = Field()
    description = Field()
    client_requirement = Field()
    team_requirement = Field()
    external_reference = Field()
    tribe_gig = Field()
    version = Field()
    blocked_note = Field()
    is_blocked = Field()
    tags = Field()
    due_date = DateTimeField()
    due_date_reason = Field()

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_userstories_attributes_cache:
            _custom_userstories_attributes_cache[project.id] = list(
                project.userstorycustomattributes.all().values('id', 'name')
            )
        return _custom_userstories_attributes_cache[project.id]

    def statuses_queryset(self, project):
        if project.id not in _userstories_statuses_cache:
            _userstories_statuses_cache[project.id] = {s.id: s.name for s in project.us_statuses.all()}
        return _userstories_statuses_cache[project.id]

    def get_assigned_users(self, obj):
        return [user.email for user in obj.assigned_users.all()]


class EpicRelatedUserStoryExportSerializer(RelatedExportSerializer):
    user_story = SlugRelatedField(slug_field="ref")
    order = Field()
    source_project_slug = MethodField()

    def get_source_project_slug(self, obj):
        if obj.epic.project.slug != obj.user_story.project.slug:
            return obj.user_story.project.slug

        return None


class EpicExportSerializer(CustomAttributesValuesExportSerializerMixin,
                           HistoryExportSerializerMixin,
                           AttachmentExportSerializerMixin,
                           WatcheableObjectLightSerializerMixin,
                           RelatedExportSerializer):
    ref = Field()
    owner = UserRelatedField()
    status = SlugRelatedField(slug_field="name")
    epics_order = Field()
    created_date = DateTimeField()
    modified_date = DateTimeField()
    subject = Field()
    description = Field()
    color = Field()
    assigned_to = UserRelatedField()
    client_requirement = Field()
    team_requirement = Field()
    version = Field()
    blocked_note = Field()
    is_blocked = Field()
    tags = Field()
    related_user_stories = MethodField()

    def get_related_user_stories(self, obj):
        return EpicRelatedUserStoryExportSerializer(obj.relateduserstory_set.filter(epic__project=obj.project), many=True).data

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_epics_attributes_cache:
            _custom_epics_attributes_cache[project.id] = list(
                project.epiccustomattributes.all().values('id', 'name')
            )
        return _custom_epics_attributes_cache[project.id]

    def statuses_queryset(self, project):
        if project.id not in _epics_statuses_cache:
            _epics_statuses_cache[project.id] = {s.id: s.name for s in project.epic_statuses.all()}
        return _epics_statuses_cache[project.id]


class IssueExportSerializer(CustomAttributesValuesExportSerializerMixin,
                            HistoryExportSerializerMixin,
                            AttachmentExportSerializerMixin,
                            WatcheableObjectLightSerializerMixin,
                            RelatedExportSerializer):
    owner = UserRelatedField()
    status = SlugRelatedField(slug_field="name")
    assigned_to = UserRelatedField()
    priority = SlugRelatedField(slug_field="name")
    severity = SlugRelatedField(slug_field="name")
    type = SlugRelatedField(slug_field="name")
    milestone = SlugRelatedField(slug_field="name")
    votes = MethodField("get_votes")
    modified_date = DateTimeField()
    created_date = DateTimeField()
    finished_date = DateTimeField()

    ref = Field()
    subject = Field()
    description = Field()
    external_reference = Field()
    version = Field()
    blocked_note = Field()
    is_blocked = Field()
    tags = Field()

    due_date = DateTimeField()
    due_date_reason = Field()

    def get_votes(self, obj):
        return [x.email for x in votes_service.get_voters(obj)]

    def custom_attributes_queryset(self, project):
        if project.id not in _custom_issues_attributes_cache:
            _custom_issues_attributes_cache[project.id] = list(project.issuecustomattributes.all().values('id', 'name'))
        return _custom_issues_attributes_cache[project.id]

    def statuses_queryset(self, project):
        if project.id not in _issues_statuses_cache:
            _issues_statuses_cache[project.id] = {s.id: s.name for s in project.issue_statuses.all()}
        return _issues_statuses_cache[project.id]

class WikiPageExportSerializer(HistoryExportSerializerMixin,
                               AttachmentExportSerializerMixin,
                               WatcheableObjectLightSerializerMixin,
                               RelatedExportSerializer):
    slug = Field()
    owner = UserRelatedField()
    last_modifier = UserRelatedField()
    modified_date = DateTimeField()
    created_date = DateTimeField()
    content = Field()
    version = Field()

    def statuses_queryset(self, project):
        return {}

class WikiLinkExportSerializer(RelatedExportSerializer):
    title = Field()
    href = Field()
    order = Field()


class TimelineExportSerializer(RelatedExportSerializer):
    data = TimelineDataField()
    data_content_type = ContentTypeField()
    event_type = Field()
    created = DateTimeField()


class ProjectExportSerializer(WatcheableObjectLightSerializerMixin):
    name = Field()
    slug = Field()
    description = Field()
    created_date = DateTimeField()
    logo = FileField()
    total_milestones = Field()
    total_story_points = Field()
    is_epics_activated = Field()
    is_backlog_activated = Field()
    is_kanban_activated = Field()
    is_wiki_activated = Field()
    is_issues_activated = Field()
    videoconferences = Field()
    videoconferences_extra_data = Field()
    creation_template = SlugRelatedField(slug_field="slug")
    is_private = Field()
    is_featured = Field()
    is_looking_for_people = Field()
    looking_for_people_note = Field()
    epics_csv_uuid = Field()
    userstories_csv_uuid = Field()
    tasks_csv_uuid = Field()
    issues_csv_uuid = Field()
    transfer_token = Field()
    blocked_code = Field()
    totals_updated_datetime = DateTimeField()
    total_fans = Field()
    total_fans_last_week = Field()
    total_fans_last_month = Field()
    total_fans_last_year = Field()
    total_activity = Field()
    total_activity_last_week = Field()
    total_activity_last_month = Field()
    total_activity_last_year = Field()
    anon_permissions = Field()
    public_permissions = Field()
    modified_date = DateTimeField()
    roles = RoleExportSerializer(many=True)
    owner = UserRelatedField()
    memberships = MembershipExportSerializer(many=True)
    points = PointsExportSerializer(many=True)
    epic_statuses = EpicStatusExportSerializer(many=True)
    us_statuses = UserStoryStatusExportSerializer(many=True)
    us_duedates = UserStoryDueDateExportSerializer(many=True)
    task_statuses = TaskStatusExportSerializer(many=True)
    task_duedates = TaskDueDateExportSerializer(many=True)
    issue_types = IssueTypeExportSerializer(many=True)
    issue_statuses = IssueStatusExportSerializer(many=True)
    issue_duedates = IssueDueDateExportSerializer(many=True)
    priorities = PriorityExportSerializer(many=True)
    severities = SeverityExportSerializer(many=True)
    swimlanes = SwimlaneExportSerializer(many=True)
    tags_colors = Field()
    default_points = SlugRelatedField(slug_field="name")
    default_epic_status = SlugRelatedField(slug_field="name")
    default_us_status = SlugRelatedField(slug_field="name")
    default_task_status = SlugRelatedField(slug_field="name")
    default_priority = SlugRelatedField(slug_field="name")
    default_severity = SlugRelatedField(slug_field="name")
    default_issue_status = SlugRelatedField(slug_field="name")
    default_issue_type = SlugRelatedField(slug_field="name")
    default_swimlane = SlugRelatedField(slug_field="name")
    epiccustomattributes = EpicCustomAttributesExportSerializer(many=True)
    userstorycustomattributes = UserStoryCustomAttributeExportSerializer(many=True)
    taskcustomattributes = TaskCustomAttributeExportSerializer(many=True)
    issuecustomattributes = IssueCustomAttributeExportSerializer(many=True)
    epics = EpicExportSerializer(many=True)
    user_stories = UserStoryExportSerializer(many=True)
    tasks = TaskExportSerializer(many=True)
    milestones = MilestoneExportSerializer(many=True)
    issues = IssueExportSerializer(many=True)
    wiki_links = WikiLinkExportSerializer(many=True)
    wiki_pages = WikiPageExportSerializer(many=True)
    tags = Field()
