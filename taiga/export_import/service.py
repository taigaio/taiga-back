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

from django.db.models import signals
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from taiga.projects.models import Project

from . import serializers

_errors_log = []

def get_errors():
    _errors = _errors_log.copy()
    _errors_log.clear()
    return _errors

def add_errors(errors):
    _errors_log.append(errors)

def project_to_dict(project):
    return serializers.ProjectExportSerializer(project).data

@transaction.atomic
def store_project(data):
    project_data = {}
    for key, value in data.items():
        excluded_fields = [
            "default_points", "default_us_status", "default_task_status",
            "default_priority", "default_severity", "default_issue_status",
            "default_issue_type", "memberships", "points", "us_statuses",
            "task_statuses", "issue_statuses", "priorities", "severities",
            "issue_types", "roles", "milestones", "wiki_pages",
            "wiki_links", "notify_policies", "user_stories", "issues"
        ]
        if key not in excluded_fields:
            project_data[key] = value

    serialized = serializers.ProjectExportSerializer(data=project_data)
    if serialized.is_valid():
        serialized.object._importing = True
        serialized.object.save()
        return serialized
    else:
        add_errors(serialized.errors)
        return None

@transaction.atomic
def store_choices(project, data, field, relation, serializer, default_field):
    relation.all().delete()

    for point in data[field]:
        serialized = serializer(data=point)
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

@transaction.atomic
def store_default_choices(project, data):
    project.default_points = project.points.all().get(name=data['default_points'])
    project.default_issue_type = project.issue_types.get(name=data['default_issue_type'])
    project.default_issue_status = project.issue_statuses.get(name=data['default_issue_status'])
    project.default_us_status = project.us_statuses.get(name=data['default_us_status'])
    project.default_task_status = project.task_statuses.get(name=data['default_task_status'])
    project.default_priority = project.priorities.get(name=data['default_priority'])
    project.default_severity = project.severities.get(name=data['default_severity'])
    project._importing = True
    project.save()

@transaction.atomic
def store_roles(project, data):
    project.roles.all().delete()
    for role in data['roles']:
        serialized = serializers.RoleExportSerializer(data=role)
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

@transaction.atomic
def store_memberships(project, data):
    for membership in data['memberships']:
        serialized = serializers.MembershipExportSerializer(data=membership, context={"project": project})
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

@transaction.atomic
def store_task(project, us, task):
    serialized = serializers.TaskExportSerializer(data=task, context={"project": project})
    serialized.is_valid()
    serialized.object.user_story = us
    serialized.object.project = project
    serialized.object._importing = True
    serialized.save()

    for task_attachment in task['attachments']:
        store_attachment(project, serialized.object, task_attachment)

@transaction.atomic
def store_milestones(project, data):
    for milestone in data['milestones']:
        serialized = serializers.MilestoneExportSerializer(data=milestone)
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

        for task_without_us in milestone['tasks_without_us']:
            store_task(project, None, task_without_us)

def store_attachment(project, obj, attachment):
    serialized = serializers.AttachmentExportSerializer(data=attachment)
    serialized.is_valid()
    serialized.object.content_type = ContentType.objects.get_for_model(obj.__class__)
    serialized.object.object_id = obj.id
    serialized.object.project = project
    serialized.object._importing = True
    serialized.save()

@transaction.atomic
def store_wiki_pages(project, data):
    for wiki_page in data['wiki_pages']:
        serialized = serializers.WikiPageExportSerializer(data=wiki_page)
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

        for attachment in wiki_page['attachments']:
            store_attachment(project, serialized.object, attachment)

@transaction.atomic
def store_wiki_links(project, data):
    for wiki_link in data['wiki_links']:
        serialized = serializers.WikiLinkExportSerializer(data=wiki_link)
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

@transaction.atomic
def store_role_point(project, us, role_point):
    serialized = serializers.RolePointsExportSerializer(data=role_point, context={"project": project} )
    serialized.is_valid()
    serialized.object.user_story = us
    serialized.save()

@transaction.atomic
def store_user_stories(project, data):
    for userstory in data['user_stories']:
        userstory_data = {}
        for key, value in userstory.items():
            excluded_fields = [
                'tasks', 'role_points'
            ]
            if key not in excluded_fields:
                userstory_data[key] = value
        serialized_us = serializers.UserStoryExportSerializer(data=userstory_data, context={"project": project})
        serialized_us.is_valid()
        serialized_us.object.project = project
        serialized_us.object._importing = True
        serialized_us.save()

        for task in userstory['tasks']:
            store_task(project, serialized_us.object, task)

        for us_attachment in userstory['attachments']:
            store_attachment(project, serialized_us.object, us_attachment)

        for role_point in userstory['role_points']:
            store_role_point(project, serialized_us.object, role_point)

@transaction.atomic
def store_issues(project, data):
    for issue in data['issues']:
        serialized = serializers.IssueExportSerializer(data=issue, context={"project": project})
        serialized.is_valid()
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

        for attachment in issue['attachments']:
            store_attachment(project, serialized.object, attachment)


def dict_to_project(data, owner=None):
    signals.pre_save.receivers = []
    signals.post_save.receivers = []
    signals.pre_delete.receivers = []
    signals.post_delete.receivers = []

    if owner:
        data['owner'] = owner

    project_serialized = store_project(data)
    store_choices(project_serialized.object, data, "points", project_serialized.object.points, serializers.PointsExportSerializer, "default_points")
    store_choices(project_serialized.object, data, "issue_types", project_serialized.object.issue_types, serializers.IssueTypeExportSerializer, "default_issue_type")
    store_choices(project_serialized.object, data, "issue_statuses", project_serialized.object.issue_statuses, serializers.IssueStatusExportSerializer, "default_issue_status")
    store_choices(project_serialized.object, data, "us_statuses", project_serialized.object.us_statuses, serializers.UserStoryStatusExportSerializer, "default_us_status")
    store_choices(project_serialized.object, data, "task_statuses", project_serialized.object.task_statuses, serializers.TaskStatusExportSerializer, "default_task_status")
    store_choices(project_serialized.object, data, "priorities", project_serialized.object.priorities, serializers.PriorityExportSerializer, "default_priority")
    store_choices(project_serialized.object, data, "severities", project_serialized.object.severities, serializers.SeverityExportSerializer, "default_severity")
    store_default_choices(project_serialized.object, data)
    store_roles(project_serialized.object, data)
    store_memberships(project_serialized.object, data)
    store_milestones(project_serialized.object, data)
    store_wiki_pages(project_serialized.object, data)
    store_wiki_links(project_serialized.object, data)

    store_user_stories(project_serialized.object, data)
    store_issues(project_serialized.object, data)
