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

import uuid
import os.path as path
from unidecode import unidecode

from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType

from taiga.projects.history.services import make_key_from_model_object
from taiga.projects.references import sequences as seq
from taiga.projects.references import models as refs
from taiga.projects.services import find_invited_user

from . import serializers

_errors_log = {}


def get_errors(clear=True):
    _errors = _errors_log.copy()
    if clear:
        _errors_log.clear()
    return _errors


def add_errors(section, errors):
    if section in _errors_log:
        _errors_log[section].append(errors)
    else:
        _errors_log[section] = [errors]

def project_to_dict(project):
    return serializers.ProjectExportSerializer(project).data


def store_project(data):
    project_data = {}
    for key, value in data.items():
        excluded_fields = [
            "default_points", "default_us_status", "default_task_status",
            "default_priority", "default_severity", "default_issue_status",
            "default_issue_type", "memberships", "points", "us_statuses",
            "task_statuses", "issue_statuses", "priorities", "severities",
            "issue_types", "roles", "milestones", "wiki_pages",
            "wiki_links", "notify_policies", "user_stories", "issues", "tasks",
        ]
        if key not in excluded_fields:
            project_data[key] = value

    serialized = serializers.ProjectExportSerializer(data=project_data)
    if serialized.is_valid():
        serialized.object._importing = True
        serialized.object.save()
        return serialized
    add_errors("project", serialized.errors)
    return None


def store_choice(project, data, field, serializer):
    serialized = serializer(data=data)
    if serialized.is_valid():
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()
        return serialized.object
    add_errors(field, serialized.errors)
    return None


def store_choices(project, data, field, serializer):
    result = []
    for choice_data in data[field]:
        result.append(store_choice(project, choice_data, field, serializer))
    return result


def store_role(project, role):
    serialized = serializers.RoleExportSerializer(data=role)
    if serialized.is_valid():
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()
        return serialized
    add_errors("roles", serialized.errors)
    return None


def store_roles(project, data):
    results = []
    for role in data['roles']:
        results.append(store_role(project, role))
    return results


def store_default_choices(project, data):
    def helper(project, field, related, data):
        if field in data:
            value = related.all().get(name=data[field])
        else:
            value = related.all().first()
        setattr(project, field, value)

    helper(project, "default_points", project.points, data)
    helper(project, "default_issue_type", project.issue_types, data)
    helper(project, "default_issue_status", project.issue_statuses, data)
    helper(project, "default_us_status", project.us_statuses, data)
    helper(project, "default_task_status", project.task_statuses, data)
    helper(project, "default_priority", project.priorities, data)
    helper(project, "default_severity", project.severities, data)
    project._importing = True
    project.save()


def store_membership(project, membership):
    serialized = serializers.MembershipExportSerializer(data=membership, context={"project": project})
    if serialized.is_valid():
        serialized.object.project = project
        serialized.object._importing = True
        if not serialized.object.token:
            serialized.object.token = str(uuid.uuid1())
        serialized.object.user = find_invited_user(serialized.object.email,
                                                   default=serialized.object.user)
        serialized.save()
        return serialized

    add_errors("memberships", serialized.errors)
    return None


def store_memberships(project, data):
    results = []
    for membership in data.get('memberships', []):
        results.append(store_membership(project, membership))
    return results


def store_task(project, task):
    if 'status' not in task and project.default_task_status:
        task['status'] = project.default_task_status.name

    serialized = serializers.TaskExportSerializer(data=task, context={"project": project})
    if serialized.is_valid():
        serialized.object.project = project
        if serialized.object.owner is None:
            serialized.object.owner = serialized.object.project.owner
        serialized.object._importing = True
        serialized.object._not_notify = True

        serialized.save()

        if serialized.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, serialized.object.ref)
        else:
            serialized.object.ref, _ = refs.make_reference(serialized.object, project)
            serialized.object.save()

        for task_attachment in task.get('attachments', []):
            store_attachment(project, serialized.object, task_attachment)

        for history in task.get('history', []):
            store_history(project, serialized.object, history)

        return serialized

    add_errors("tasks", serialized.errors)
    return None


def store_milestone(project, milestone):
    serialized = serializers.MilestoneExportSerializer(data=milestone, project=project)
    if serialized.is_valid():
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()

        for task_without_us in milestone.get('tasks_without_us', []):
            task_without_us['user_story'] = None
            store_task(project, task_without_us)
        return serialized

    add_errors("milestones", serialized.errors)
    return None


def store_attachment(project, obj, attachment):
    serialized = serializers.AttachmentExportSerializer(data=attachment)
    if serialized.is_valid():
        serialized.object.content_type = ContentType.objects.get_for_model(obj.__class__)
        serialized.object.object_id = obj.id
        serialized.object.project = project
        if serialized.object.owner is None:
            serialized.object.owner = serialized.object.project.owner
        serialized.object._importing = True
        serialized.object.size = serialized.object.attached_file.size
        serialized.object.name = path.basename(serialized.object.attached_file.name).lower()
        serialized.save()
        return serialized
    add_errors("attachments", serialized.errors)
    return serialized


def store_history(project, obj, history):
    serialized = serializers.HistoryExportSerializer(data=history, context={"project": project})
    if serialized.is_valid():
        serialized.object.key = make_key_from_model_object(obj)
        if serialized.object.diff is None:
            serialized.object.diff = []
        serialized.object._importing = True
        serialized.save()
        return serialized
    add_errors("history", serialized.errors)
    return serialized


def store_wiki_page(project, wiki_page):
    wiki_page['slug'] = slugify(unidecode(wiki_page.get('slug', '')))
    serialized = serializers.WikiPageExportSerializer(data=wiki_page)
    if serialized.is_valid():
        serialized.object.project = project
        if serialized.object.owner is None:
            serialized.object.owner = serialized.object.project.owner
        serialized.object._importing = True
        serialized.object._not_notify = True
        serialized.save()

        for attachment in wiki_page.get('attachments', []):
            store_attachment(project, serialized.object, attachment)

        for history in wiki_page.get('history', []):
            store_history(project, serialized.object, history)

        return serialized

    add_errors("wiki_pages", serialized.errors)
    return None


def store_wiki_link(project, wiki_link):
    serialized = serializers.WikiLinkExportSerializer(data=wiki_link)
    if serialized.is_valid():
        serialized.object.project = project
        serialized.object._importing = True
        serialized.save()
        return serialized

    add_errors("wiki_links", serialized.errors)
    return None


def store_role_point(project, us, role_point):
    serialized = serializers.RolePointsExportSerializer(data=role_point, context={"project": project})
    if serialized.is_valid():
        serialized.object.user_story = us
        serialized.save()
        return serialized.object
    add_errors("role_points", serialized.errors)
    return None


def store_user_story(project, userstory):
    if 'status' not in userstory and project.default_us_status:
        userstory['status'] = project.default_us_status.name

    userstory_data = {}
    for key, value in userstory.items():
        if key != 'role_points':
            userstory_data[key] = value
    serialized_us = serializers.UserStoryExportSerializer(data=userstory_data, context={"project": project})
    if serialized_us.is_valid():
        serialized_us.object.project = project
        if serialized_us.object.owner is None:
            serialized_us.object.owner = serialized_us.object.project.owner
        serialized_us.object._importing = True
        serialized_us.object._not_notify = True

        serialized_us.save()

        if serialized_us.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, serialized_us.object.ref)
        else:
            serialized_us.object.ref, _ = refs.make_reference(serialized_us.object, project)
            serialized_us.object.save()

        for us_attachment in userstory.get('attachments', []):
            store_attachment(project, serialized_us.object, us_attachment)

        for role_point in userstory.get('role_points', []):
            store_role_point(project, serialized_us.object, role_point)

        for history in userstory.get('history', []):
            store_history(project, serialized_us.object, history)

        return serialized_us
    add_errors("user_stories", serialized_us.errors)
    return None


def store_issue(project, data):
    serialized = serializers.IssueExportSerializer(data=data, context={"project": project})

    if 'type' not in data and project.default_issue_type:
        data['type'] = project.default_issue_type.name

    if 'status' not in data and project.default_issue_status:
        data['status'] = project.default_issue_status.name

    if 'priority' not in data and project.default_priority:
        data['priority'] = project.default_priority.name

    if 'severity' not in data and project.default_severity:
        data['severity'] = project.default_severity.name

    if serialized.is_valid():
        serialized.object.project = project
        if serialized.object.owner is None:
            serialized.object.owner = serialized.object.project.owner
        serialized.object._importing = True
        serialized.object._not_notify = True

        serialized.save()

        if serialized.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, serialized.object.ref)
        else:
            serialized.object.ref, _ = refs.make_reference(serialized.object, project)
            serialized.object.save()

        for attachment in data.get('attachments', []):
            store_attachment(project, serialized.object, attachment)
        for history in data.get('history', []):
            store_history(project, serialized.object, history)
        return serialized
    add_errors("issues", serialized.errors)
    return None
