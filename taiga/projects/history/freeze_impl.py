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

from contextlib import suppress

from functools import partial
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails.exceptions import InvalidImageFormatError

from taiga.base.utils.urls import get_absolute_url
from taiga.base.utils.iterators import as_tuple
from taiga.base.utils.iterators import as_dict
from taiga.mdrender.service import render as mdrender

import os

####################
# Values
####################

@as_dict
def _get_generic_values(ids:tuple, *, typename=None, attr:str="name") -> tuple:
    app_label, model_name = typename.split(".", 1)
    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
    model_cls = content_type.model_class()

    ids = filter(lambda x: x is not None, ids)
    qs = model_cls.objects.filter(pk__in=ids)
    for instance in qs:
        yield str(instance.pk), getattr(instance, attr)


@as_dict
def _get_users_values(ids:set) -> dict:
    user_model = apps.get_model("users", "User")
    ids = filter(lambda x: x is not None, ids)
    qs = user_model.objects.filter(pk__in=tuple(ids))

    for user in qs:
        yield str(user.pk), user.get_full_name()


@as_dict
def _get_user_story_values(ids:set) -> dict:
    userstory_model = apps.get_model("userstories", "UserStory")
    ids = filter(lambda x: x is not None, ids)
    qs = userstory_model.objects.filter(pk__in=tuple(ids))

    for userstory in qs:
        yield str(userstory.pk), "#{} {}".format(userstory.ref, userstory.subject)


_get_us_status_values = partial(_get_generic_values, typename="projects.userstorystatus")
_get_task_status_values = partial(_get_generic_values, typename="projects.taskstatus")
_get_issue_status_values = partial(_get_generic_values, typename="projects.issuestatus")
_get_issue_type_values = partial(_get_generic_values, typename="projects.issuetype")
_get_role_values = partial(_get_generic_values, typename="users.role")
_get_points_values = partial(_get_generic_values, typename="projects.points")
_get_priority_values = partial(_get_generic_values, typename="projects.priority")
_get_severity_values = partial(_get_generic_values, typename="projects.severity")
_get_milestone_values = partial(_get_generic_values, typename="milestones.milestone")


def _common_users_values(diff):
    """
    Groups common values resolver logic of userstories,
    issues and tasks.
    """
    values = {}
    users = set()

    if "owner" in diff:
        users.update(diff["owner"])
    if "assigned_to" in diff:
        users.update(diff["assigned_to"])
    if users:
        values["users"] = _get_users_values(users)

    return values

def project_values(diff):
    values = _common_users_values(diff)
    return values


def milestone_values(diff):
    values = _common_users_values(diff)
    return values


def userstory_values(diff):
    values = _common_users_values(diff)

    if "status" in diff:
        values["status"] = _get_us_status_values(diff["status"])
    if "milestone" in diff:
        values["milestone"] = _get_milestone_values(diff["milestone"])
    if "points" in diff:
        points, roles = set(), set()

        for pointsentry in diff["points"]:
            if pointsentry is None:
                continue

            for role_id, point_id in pointsentry.items():
                points.add(point_id)
                roles.add(role_id)

        values["roles"] = _get_role_values(roles)
        values["points"] = _get_points_values(points)

    return values


def issue_values(diff):
    values = _common_users_values(diff)

    if "status" in diff:
        values["status"] = _get_issue_status_values(diff["status"])
    if "milestone" in diff:
        values["milestone"] = _get_milestone_values(diff["milestone"])
    if "priority" in diff:
        values["priority"] = _get_priority_values(diff["priority"])
    if "severity" in diff:
        values["severity"] = _get_severity_values(diff["severity"])
    if "type" in diff:
        values["type"] = _get_issue_type_values(diff["type"])

    return values


def task_values(diff):
    values = _common_users_values(diff)

    if "status" in diff:
        values["status"] = _get_task_status_values(diff["status"])
    if "milestone" in diff:
        values["milestone"] = _get_milestone_values(diff["milestone"])
    if "user_story" in diff:
        values["user_story"] = _get_user_story_values(diff["user_story"])

    return values


def wikipage_values(diff):
    values = _common_users_values(diff)
    return values


####################
# Freezes
####################

def _generic_extract(obj:object, fields:list, default=None) -> dict:
    result = {}
    for fieldname in fields:
        result[fieldname] = getattr(obj, fieldname, default)
    return result


@as_tuple
def extract_attachments(obj) -> list:
    for attach in obj.attachments.all():
        try:
            thumb_url = get_thumbnailer(attach.attached_file)['timeline-image'].url
            thumb_url = get_absolute_url(thumb_url)
        except InvalidImageFormatError as e:
            thumb_url = None

        yield {"id": attach.id,
               "filename": os.path.basename(attach.attached_file.name),
               "url": attach.attached_file.url,
               "thumb_url": thumb_url,
               "is_deprecated": attach.is_deprecated,
               "description": attach.description,
               "order": attach.order}


@as_tuple
def extract_user_story_custom_attributes(obj) -> list:
    with suppress(ObjectDoesNotExist):
        custom_attributes_values =  obj.custom_attributes_values.attributes_values
        for attr in obj.project.userstorycustomattributes.all():
            with suppress(KeyError):
                value = custom_attributes_values[str(attr.id)]
                yield {"id": attr.id,
                       "name": attr.name,
                       "value": value}


@as_tuple
def extract_task_custom_attributes(obj) -> list:
    with suppress(ObjectDoesNotExist):
        custom_attributes_values =  obj.custom_attributes_values.attributes_values
        for attr in obj.project.taskcustomattributes.all():
            with suppress(KeyError):
                value = custom_attributes_values[str(attr.id)]
                yield {"id": attr.id,
                       "name": attr.name,
                       "value": value}


@as_tuple
def extract_issue_custom_attributes(obj) -> list:
    with suppress(ObjectDoesNotExist):
        custom_attributes_values =  obj.custom_attributes_values.attributes_values
        for attr in obj.project.issuecustomattributes.all():
            with suppress(KeyError):
                value = custom_attributes_values[str(attr.id)]
                yield {"id": attr.id,
                       "name": attr.name,
                       "value": value}


def project_freezer(project) -> dict:
    fields = ("name",
              "slug",
              "created_at",
              "owner_id",
              "public",
              "total_milestones",
              "total_story_points",
              "tags",
              "is_backlog_activated",
              "is_kanban_activated",
              "is_wiki_activated",
              "is_issues_activated")
    return _generic_extract(project, fields)


def milestone_freezer(milestone) -> dict:
    snapshot = {
        "name": milestone.name,
        "slug": milestone.slug,
        "owner": milestone.owner_id,
        "estimated_start": milestone.estimated_start,
        "estimated_finish": milestone.estimated_finish,
        "closed": milestone.closed,
        "disponibility": milestone.disponibility
    }

    return snapshot


def userstory_freezer(us) -> dict:
    rp_cls = apps.get_model("userstories", "RolePoints")
    rpqsd = rp_cls.objects.filter(user_story=us)

    points = {}
    for rp in rpqsd:
        points[str(rp.role_id)] = rp.points_id

    snapshot = {
        "ref": us.ref,
        "owner": us.owner_id,
        "status": us.status_id,
        "is_closed": us.is_closed,
        "finish_date": str(us.finish_date),
        "backlog_order": us.backlog_order,
        "sprint_order": us.sprint_order,
        "kanban_order": us.kanban_order,
        "subject": us.subject,
        "description": us.description,
        "description_html": mdrender(us.project, us.description),
        "assigned_to": us.assigned_to_id,
        "milestone": us.milestone_id,
        "client_requirement": us.client_requirement,
        "team_requirement": us.team_requirement,
        "attachments": extract_attachments(us),
        "tags": us.tags,
        "points": points,
        "from_issue": us.generated_from_issue_id,
        "is_blocked": us.is_blocked,
        "blocked_note": us.blocked_note,
        "blocked_note_html": mdrender(us.project, us.blocked_note),
        "custom_attributes": extract_user_story_custom_attributes(us),
    }

    return snapshot


def issue_freezer(issue) -> dict:
    snapshot = {
        "ref": issue.ref,
        "owner": issue.owner_id,
        "status": issue.status_id,
        "priority": issue.priority_id,
        "severity": issue.severity_id,
        "type": issue.type_id,
        "milestone": issue.milestone_id,
        "subject": issue.subject,
        "description": issue.description,
        "description_html": mdrender(issue.project, issue.description),
        "assigned_to": issue.assigned_to_id,
        "attachments": extract_attachments(issue),
        "tags": issue.tags,
        "is_blocked": issue.is_blocked,
        "blocked_note": issue.blocked_note,
        "blocked_note_html": mdrender(issue.project, issue.blocked_note),
        "custom_attributes": extract_issue_custom_attributes(issue),
    }

    return snapshot


def task_freezer(task) -> dict:
    snapshot = {
        "ref": task.ref,
        "owner": task.owner_id,
        "status": task.status_id,
        "milestone": task.milestone_id,
        "subject": task.subject,
        "description": task.description,
        "description_html": mdrender(task.project, task.description),
        "assigned_to": task.assigned_to_id,
        "attachments": extract_attachments(task),
        "taskboard_order": task.taskboard_order,
        "us_order": task.us_order,
        "tags": task.tags,
        "user_story": task.user_story_id,
        "is_iocaine": task.is_iocaine,
        "is_blocked": task.is_blocked,
        "blocked_note": task.blocked_note,
        "blocked_note_html": mdrender(task.project, task.blocked_note),
        "custom_attributes": extract_task_custom_attributes(task),
    }

    return snapshot


def wikipage_freezer(wiki) -> dict:
    snapshot = {
        "slug": wiki.slug,
        "owner": wiki.owner_id,
        "content": wiki.content,
        "content_html": mdrender(wiki.project, wiki.content),
        "attachments": extract_attachments(wiki),
    }

    return snapshot
