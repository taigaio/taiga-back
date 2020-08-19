# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

# This makes all code that import services works and
# is not the baddest practice ;)

import os
import uuid

from unidecode import unidecode

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import utils
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from taiga.projects.history.services import make_key_from_model_object, take_snapshot
from taiga.projects.models import Membership
from taiga.projects.references import sequences as seq
from taiga.projects.references import models as refs
from taiga.projects.userstories.models import RolePoints
from taiga.projects.services import find_invited_user
from taiga.timeline.service import build_project_namespace
from taiga.users import services as users_service

from .. import exceptions as err
from .. import validators


########################################################################
## Manage errors
########################################################################

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


def reset_errors():
    _errors_log.clear()


########################################################################
## Store functions
########################################################################


## PROJECT

def store_project(data):
    project_data = {}
    for key, value in data.items():
        excluded_fields = [
            "default_points", "default_us_status", "default_task_status",
            "default_priority", "default_severity", "default_issue_status",
            "default_issue_type", "default_epic_status",
            "memberships", "points",
            "epic_statuses", "us_statuses", "task_statuses", "issue_statuses",
            "priorities", "severities",
            "issue_types",
            "epiccustomattributes", "userstorycustomattributes",
            "taskcustomattributes", "issuecustomattributes",
            "roles", "milestones",
            "wiki_pages", "wiki_links",
            "notify_policies",
            "epics", "user_stories", "issues", "tasks",
            "is_featured"
        ]
        if key not in excluded_fields:
            project_data[key] = value

    validator = validators.ProjectExportValidator(data=project_data)
    if validator.is_valid():
        validator.object._importing = True
        validator.object.save()
        validator.save_watchers()
        return validator
    add_errors("project", validator.errors)
    return None


## MISC

def _use_id_instead_name_as_key_in_custom_attributes_values(custom_attributes, values):
    ret = {}
    for attr in custom_attributes:
        value = values.get(attr["name"], None)
        if value is not None:
            ret[str(attr["id"])] = value

    return ret


def _store_custom_attributes_values(obj, data_values, obj_field, serializer_class):
    data = {
        obj_field: obj.id,
        "attributes_values": data_values,
    }

    try:
        custom_attributes_values = obj.custom_attributes_values
        serializer = serializer_class(custom_attributes_values, data=data)
    except ObjectDoesNotExist:
        serializer = serializer_class(data=data)

    if serializer.is_valid():
        serializer.save()
        return serializer

    add_errors("custom_attributes_values", serializer.errors)
    return None


def _store_attachment(project, obj, attachment):
    validator = validators.AttachmentExportValidator(data=attachment)
    if validator.is_valid():
        validator.object.content_type = ContentType.objects.get_for_model(obj.__class__)
        validator.object.object_id = obj.id
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object.size = validator.object.attached_file.size
        validator.object.name = os.path.basename(validator.object.attached_file.name)
        validator.save()
        return validator
    add_errors("attachments", validator.errors)
    return validator


def _store_history(project, obj, history, statuses={}):
    validator = validators.HistoryExportValidator(data=history, context={"project": project, "statuses": statuses})
    if validator.is_valid():
        validator.object.key = make_key_from_model_object(obj)
        if validator.object.diff is None:
            validator.object.diff = []
        validator.object.project_id = project.id
        validator.object._importing = True
        validator.save()
        return validator
    add_errors("history", validator.errors)
    return validator


## ROLES

def _store_role(project, role):
    validator = validators.RoleExportValidator(data=role)
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.save()
        return validator
    add_errors("roles", validator.errors)
    return None


def store_roles(project, data):
    results = []
    for role in data.get("roles", []):
        validator = _store_role(project, role)
        if validator:
            results.append(validator)

    return results


## MEMGERSHIPS

def _store_membership(project, membership):
    validator = validators.MembershipExportValidator(data=membership, context={"project": project})
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.object.token = str(uuid.uuid1())
        validator.object.user = find_invited_user(validator.object.email,
                                                  default=validator.object.user)
        try:
            validator.save()
        except utils.IntegrityError:
            # Avoid import errors when the project has duplicated invitations
            return
        return validator

    add_errors("memberships", validator.errors)
    return None


def store_memberships(project, data):
    results = []
    for membership in data.get("memberships", []):
        member = _store_membership(project, membership)
        if member:
            results.append(member)
    return results


## PROJECT ATTRIBUTES

def _store_project_attribute_value(project, data, field, serializer):
    validator = serializer(data=data)
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.save()
        return validator.object

    add_errors(field, validator.errors)
    return None


def store_project_attributes_values(project, data, field, serializer):
    result = []
    for choice_data in data.get(field, []):
        result.append(_store_project_attribute_value(project, choice_data, field,
                                                     serializer))
    return result


## DEFAULT PROJECT ATTRIBUTES VALUES

def store_default_project_attributes_values(project, data):
    def helper(project, field, related, data):
        if field in data:
            value = related.all().get(name=data[field])
        else:
            value = related.all().first()
        setattr(project, field, value)
    helper(project, "default_points", project.points, data)
    helper(project, "default_issue_type", project.issue_types, data)
    helper(project, "default_issue_status", project.issue_statuses, data)
    helper(project, "default_epic_status", project.epic_statuses, data)
    helper(project, "default_us_status", project.us_statuses, data)
    helper(project, "default_task_status", project.task_statuses, data)
    helper(project, "default_priority", project.priorities, data)
    helper(project, "default_severity", project.severities, data)
    project._importing = True
    project.save()


## CUSTOM ATTRIBUTES

def _store_custom_attribute(project, data, field, serializer):
    validator = serializer(data=data)
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.save()
        return validator.object
    add_errors(field, validator.errors)
    return None


def store_custom_attributes(project, data, field, serializer):
    result = []
    for custom_attribute_data in data.get(field, []):
        result.append(_store_custom_attribute(project, custom_attribute_data, field, serializer))
    return result


## MILESTONE

def store_milestone(project, milestone):
    validator = validators.MilestoneExportValidator(data=milestone, project=project)
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.save()
        validator.save_watchers()

        for task_without_us in milestone.get("tasks_without_us", []):
            task_without_us["user_story"] = None
            store_task(project, task_without_us)
        return validator

    add_errors("milestones", validator.errors)
    return None


def store_milestones(project, data):
    results = []
    for milestone_data in data.get("milestones", []):
        milestone = store_milestone(project, milestone_data)
        results.append(milestone)
    return results


## USER STORIES

def _store_role_point(project, us, role_point):
    validator = validators.RolePointsExportValidator(data=role_point, context={"project": project})
    if validator.is_valid():
        try:
            existing_role_point = us.role_points.get(role=validator.object.role)
            existing_role_point.points = validator.object.points
            existing_role_point.save()
            return existing_role_point

        except RolePoints.DoesNotExist:
            validator.object.user_story = us
            validator.save()
            return validator.object

    add_errors("role_points", validator.errors)
    return None


def store_user_story(project, data):
    if "status" not in data and project.default_us_status:
        data["status"] = project.default_us_status.name

    us_data = {key: value for key, value in data.items() if key not in
               ["role_points", "custom_attributes_values", 'generated_from_task', 'generated_from_issue']}

    validator = validators.UserStoryExportValidator(data=us_data, context={"project": project})

    if validator.is_valid():
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object._not_notify = True

        validator.save()
        validator.save_watchers()

        if validator.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, validator.object.ref)
        else:
            validator.object.ref, _ = refs.make_reference(validator.object, project)
            validator.object.save()

        for us_attachment in data.get("attachments", []):
            _store_attachment(project, validator.object, us_attachment)

        for role_point in data.get("role_points", []):
            _store_role_point(project, validator.object, role_point)

        history_entries = data.get("history", [])
        statuses = {s.name: s.id for s in project.us_statuses.all()}
        for history in history_entries:
            _store_history(project, validator.object, history, statuses)

        if not history_entries:
            take_snapshot(validator.object, user=validator.object.owner)

        custom_attributes_values = data.get("custom_attributes_values", None)
        if custom_attributes_values:
            custom_attributes = validator.object.project.userstorycustomattributes.all().values('id', 'name')
            custom_attributes_values = \
                _use_id_instead_name_as_key_in_custom_attributes_values(custom_attributes,
                                                                        custom_attributes_values)

            _store_custom_attributes_values(validator.object, custom_attributes_values,
                                            "user_story",
                                            validators.UserStoryCustomAttributesValuesExportValidator)

        return validator

    add_errors("user_stories", validator.errors)
    return None


def store_user_stories(project, data):
    user_stories = {}
    for userstory in data.get("user_stories", []):
        validator = store_user_story(project, userstory)
        if validator:
            user_stories[validator.object.ref] = validator.object
    return user_stories


def store_user_stories_related_entities(imported_user_stories,
                                        imported_tasks,
                                        imported_issues,
                                        data):
    for us_data in data.get("user_stories", []):
        us = imported_user_stories.get(us_data.get('ref'))
        if not us or \
                not (us_data.get('generated_from_task')
                     or us_data.get('generated_from_issue')):
            continue

        if us_data.get('generated_from_task'):
            generated_from_task_ref = int(us_data.get('generated_from_task'))
            us.generated_from_task = imported_tasks.get(generated_from_task_ref)

        if us_data.get('generated_from_issue'):
            generated_from_issue_ref = int(us_data.get('generated_from_issue'))
            us.generated_from_issue = imported_issues.get(generated_from_issue_ref)

        us.save()


## EPICS

def _store_epic_related_user_story(project, epic, related_user_story):
    validator = validators.EpicRelatedUserStoryExportValidator(data=related_user_story,
                                                               context={"project": project})
    if validator.is_valid():
        validator.object.epic = epic
        validator.object.save()
        return validator.object

    add_errors("epic_related_user_stories", validator.errors)
    return None


def store_epic(project, data):
    if "status" not in data and project.default_epic_status:
        data["status"] = project.default_epic_status.name

    validator = validators.EpicExportValidator(data=data, context={"project": project})
    if validator.is_valid():
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object._not_notify = True

        validator.save()
        validator.save_watchers()

        if validator.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, validator.object.ref)
        else:
            validator.object.ref, _ = refs.make_reference(validator.object, project)
            validator.object.save()

        for epic_attachment in data.get("attachments", []):
            _store_attachment(project, validator.object, epic_attachment)

        for related_user_story in data.get("related_user_stories", []):
            _store_epic_related_user_story(project, validator.object, related_user_story)

        history_entries = data.get("history", [])
        statuses = {s.name: s.id for s in project.epic_statuses.all()}
        for history in history_entries:
            _store_history(project, validator.object, history, statuses)

        if not history_entries:
            take_snapshot(validator.object, user=validator.object.owner)

        custom_attributes_values = data.get("custom_attributes_values", None)
        if custom_attributes_values:
            custom_attributes = validator.object.project.epiccustomattributes.all().values('id', 'name')
            custom_attributes_values = \
                _use_id_instead_name_as_key_in_custom_attributes_values(custom_attributes,
                                                                        custom_attributes_values)
            _store_custom_attributes_values(validator.object, custom_attributes_values,
                                            "epic",
                                            validators.EpicCustomAttributesValuesExportValidator)

        return validator

    add_errors("epics", validator.errors)
    return None


def store_epics(project, data):
    results = []
    for epic in data.get("epics", []):
        epic = store_epic(project, epic)
        results.append(epic)
    return results


## TASKS

def store_task(project, data):
    if "status" not in data and project.default_task_status:
        data["status"] = project.default_task_status.name

    validator = validators.TaskExportValidator(data=data, context={"project": project})
    if validator.is_valid():
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object._not_notify = True

        validator.save()
        validator.save_watchers()

        if validator.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, validator.object.ref)
        else:
            validator.object.ref, _ = refs.make_reference(validator.object, project)
            validator.object.save()

        for task_attachment in data.get("attachments", []):
            _store_attachment(project, validator.object, task_attachment)

        history_entries = data.get("history", [])
        statuses = {s.name: s.id for s in project.task_statuses.all()}
        for history in history_entries:
            _store_history(project, validator.object, history, statuses)

        if not history_entries:
            take_snapshot(validator.object, user=validator.object.owner)

        custom_attributes_values = data.get("custom_attributes_values", None)
        if custom_attributes_values:
            custom_attributes = validator.object.project.taskcustomattributes.all().values('id', 'name')
            custom_attributes_values = \
                _use_id_instead_name_as_key_in_custom_attributes_values(custom_attributes,
                                                                        custom_attributes_values)

            _store_custom_attributes_values(validator.object, custom_attributes_values,
                                            "task",
                                            validators.TaskCustomAttributesValuesExportValidator)

        return validator

    add_errors("tasks", validator.errors)
    return None


def store_tasks(project, data):
    tasks = {}
    for task in data.get("tasks", []):
        validator = store_task(project, task)
        if validator:
            tasks[validator.object.ref] = validator.object
    return tasks


## ISSUES

def store_issue(project, data):
    validator = validators.IssueExportValidator(data=data, context={"project": project})

    if "type" not in data and project.default_issue_type:
        data["type"] = project.default_issue_type.name

    if "status" not in data and project.default_issue_status:
        data["status"] = project.default_issue_status.name

    if "priority" not in data and project.default_priority:
        data["priority"] = project.default_priority.name

    if "severity" not in data and project.default_severity:
        data["severity"] = project.default_severity.name

    if validator.is_valid():
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object._not_notify = True

        validator.save()
        validator.save_watchers()

        if validator.object.ref:
            sequence_name = refs.make_sequence_name(project)
            if not seq.exists(sequence_name):
                seq.create(sequence_name)
            seq.set_max(sequence_name, validator.object.ref)
        else:
            validator.object.ref, _ = refs.make_reference(validator.object, project)
            validator.object.save()

        for attachment in data.get("attachments", []):
            _store_attachment(project, validator.object, attachment)

        history_entries = data.get("history", [])
        statuses = {s.name: s.id for s in project.issue_statuses.all()}
        for history in history_entries:
            _store_history(project, validator.object, history, statuses)

        if not history_entries:
            take_snapshot(validator.object, user=validator.object.owner)

        custom_attributes_values = data.get("custom_attributes_values", None)
        if custom_attributes_values:
            custom_attributes = validator.object.project.issuecustomattributes.all().values('id', 'name')
            custom_attributes_values = \
                _use_id_instead_name_as_key_in_custom_attributes_values(custom_attributes,
                                                                        custom_attributes_values)
            _store_custom_attributes_values(validator.object, custom_attributes_values,
                                            "issue",
                                            validators.IssueCustomAttributesValuesExportValidator)

        return validator

    add_errors("issues", validator.errors)
    return None


def store_issues(project, data):
    issues = {}
    for issue in data.get("issues", []):
        validator = store_issue(project, issue)
        if validator:
            issues[validator.object.ref] = validator.object
    return issues


## WIKI PAGES

def store_wiki_page(project, wiki_page):
    wiki_page["slug"] = slugify(unidecode(wiki_page.get("slug", "")))
    validator = validators.WikiPageExportValidator(data=wiki_page)
    if validator.is_valid():
        validator.object.project = project
        if validator.object.owner is None:
            validator.object.owner = validator.object.project.owner
        validator.object._importing = True
        validator.object._not_notify = True
        validator.save()
        validator.save_watchers()

        for attachment in wiki_page.get("attachments", []):
            _store_attachment(project, validator.object, attachment)

        history_entries = wiki_page.get("history", [])
        for history in history_entries:
            _store_history(project, validator.object, history)

        if not history_entries:
            take_snapshot(validator.object, user=validator.object.owner)

        return validator

    add_errors("wiki_pages", validator.errors)
    return None


def store_wiki_pages(project, data):
    results = []
    for wiki_page in data.get("wiki_pages", []):
        results.append(store_wiki_page(project, wiki_page))
    return results


## WIKI LINKS

def store_wiki_link(project, wiki_link):
    validator = validators.WikiLinkExportValidator(data=wiki_link)
    if validator.is_valid():
        validator.object.project = project
        validator.object._importing = True
        validator.save()
        return validator

    add_errors("wiki_links", validator.errors)
    return None


def store_wiki_links(project, data):
    results = []
    for wiki_link in data.get("wiki_links", []):
        results.append(store_wiki_link(project, wiki_link))
    return results


## TAGS COLORS

def store_tags_colors(project, data):
    project.tags_colors = data.get("tags_colors", [])
    project.save()
    return None


## TIMELINE

def _store_timeline_entry(project, timeline):
    validator = validators.TimelineExportValidator(data=timeline, context={"project": project})
    if validator.is_valid():
        validator.object.project = project
        validator.object.namespace = build_project_namespace(project)
        validator.object.object_id = project.id
        validator.object.content_type = ContentType.objects.get_for_model(project.__class__)
        validator.object._importing = True
        validator.save()
        return validator
    add_errors("timeline", validator.errors)
    return validator


def store_timeline_entries(project, data):
    results = []
    for timeline in data.get("timeline", []):
        tl = _store_timeline_entry(project, timeline)
        results.append(tl)
    return results


#############################################
## Store project dict
#############################################


def _validate_if_owner_have_enought_space_to_this_project(owner, data):
    # Validate if the owner can have this project
    data["owner"] = owner.email

    is_private = data.get("is_private", False)
    total_memberships = len([m for m in data.get("memberships", [])
                            if m.get("email", None) != data["owner"]])

    total_memberships = total_memberships + 1  # 1 is the owner
    (enough_slots, error_message) = users_service.has_available_slot_for_new_project(
        owner,
        is_private,
        total_memberships
    )
    if not enough_slots:
        raise err.TaigaImportError(error_message, None)


def _create_project_object(data):
    # Create the project
    project_validator = store_project(data)

    if not project_validator:
        errors = get_errors(clear=True)
        raise err.TaigaImportError(_("error importing project data"), None, errors=errors)

    return project_validator.object if project_validator else None


def _create_membership_for_project_owner(project):
    owner_membership = project.memberships.filter(user=project.owner).first()
    if owner_membership is None:
        if project.roles.all().count() > 0:
            Membership.objects.create(
                project=project,
                email=project.owner.email,
                user=project.owner,
                role=project.roles.all().first(),
                is_admin=True
            )
    elif not owner_membership.is_admin:
            owner_membership.is_admin = True
            owner_membership.save()


def _populate_project_object(project, data):
    def check_if_there_is_some_error(message=_("error importing project data"), project=None):
        errors = get_errors(clear=True)
        if errors:
            raise err.TaigaImportError(message, project, errors=errors)

    # Create roles
    store_roles(project, data)
    check_if_there_is_some_error(_("error importing roles"), None)

    # Create memberships
    store_memberships(project, data)
    _create_membership_for_project_owner(project)
    check_if_there_is_some_error(_("error importing memberships"), project)

    # Create project attributes values
    store_project_attributes_values(project, data, "epic_statuses", validators.EpicStatusExportValidator)
    store_project_attributes_values(project, data, "us_statuses", validators.UserStoryStatusExportValidator)
    store_project_attributes_values(project, data, "points", validators.PointsExportValidator)
    store_project_attributes_values(project, data, "task_statuses", validators.TaskStatusExportValidator)
    store_project_attributes_values(project, data, "issue_types", validators.IssueTypeExportValidator)
    store_project_attributes_values(project, data, "issue_statuses", validators.IssueStatusExportValidator)
    store_project_attributes_values(project, data, "priorities", validators.PriorityExportValidator)
    store_project_attributes_values(project, data, "severities", validators.SeverityExportValidator)
    store_project_attributes_values(project, data, "us_duedates", validators.UserStoryDueDateExportValidator)
    store_project_attributes_values(project, data, "task_duedates", validators.TaskDueDateExportValidator)
    store_project_attributes_values(project, data, "issue_duedates", validators.IssueDueDateExportValidator)
    check_if_there_is_some_error(_("error importing lists of project attributes"), project)

    # Create default values for project attributes
    store_default_project_attributes_values(project, data)
    check_if_there_is_some_error(_("error importing default project attribute values"), project)

    # Create custom attributes
    store_custom_attributes(project, data, "epiccustomattributes",
                            validators.EpicCustomAttributeExportValidator)
    store_custom_attributes(project, data, "userstorycustomattributes",
                            validators.UserStoryCustomAttributeExportValidator)
    store_custom_attributes(project, data, "taskcustomattributes",
                            validators.TaskCustomAttributeExportValidator)
    store_custom_attributes(project, data, "issuecustomattributes",
                            validators.IssueCustomAttributeExportValidator)
    check_if_there_is_some_error(_("error importing custom attributes"), project)
    # Create milestones
    store_milestones(project, data)
    check_if_there_is_some_error(_("error importing sprints"), project)

    # Create issues
    imported_issues = store_issues(project, data)
    check_if_there_is_some_error(_("error importing issues"), project)

    # Create user stories
    imported_user_stories = store_user_stories(project, data)
    check_if_there_is_some_error(_("error importing user stories"), project)

    # Create epics
    store_epics(project, data)
    check_if_there_is_some_error(_("error importing epics"), project)

    # Create tasks
    imported_tasks = store_tasks(project, data)
    check_if_there_is_some_error(_("error importing tasks"), project)

    # Create user stories relationships
    store_user_stories_related_entities(imported_user_stories, imported_tasks, imported_issues, data)

    # Create wiki pages
    store_wiki_pages(project, data)
    check_if_there_is_some_error(_("error importing wiki pages"), project)

    # Create wiki links
    store_wiki_links(project, data)
    check_if_there_is_some_error(_("error importing wiki links"), project)

    # Create tags
    store_tags_colors(project, data)
    check_if_there_is_some_error(_("error importing tags"), project)

    # Create timeline
    store_timeline_entries(project, data)
    check_if_there_is_some_error(_("error importing timelines"), project)

    # Regenerate stats
    project.refresh_totals()


def store_project_from_dict(data, owner=None):
    # Validate
    if owner:
        _validate_if_owner_have_enought_space_to_this_project(owner, data)

    # Create project
    project = _create_project_object(data)

    # Populate project
    try:
        _populate_project_object(project, data)
    except err.TaigaImportError:
        # raise known inport errors
        raise
    except Exception as e:
        # raise unknown errors as import error
        raise err.TaigaImportError(_("unexpected error importing project"), project)

    return project
