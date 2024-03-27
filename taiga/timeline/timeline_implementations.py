# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.timeline.service import register_timeline_implementation
from . import service


@register_timeline_implementation("projects.project", "create")
@register_timeline_implementation("projects.project", "change")
@register_timeline_implementation("projects.project", "delete")
def project_timeline(instance, extra_data={}):
    result = {
        "project": service.extract_project_info(instance),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("milestones.milestone", "create")
@register_timeline_implementation("milestones.milestone", "change")
@register_timeline_implementation("milestones.milestone", "delete")
def milestone_timeline(instance, extra_data={}):
    result = {
        "milestone": service.extract_milestone_info(instance),
        "project": service.extract_project_info(instance.project),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("epics.epic", "create")
@register_timeline_implementation("epics.epic", "change")
@register_timeline_implementation("epics.epic", "delete")
def epic_timeline(instance, extra_data={}):
    result = {
        "epic": service.extract_epic_info(instance),
        "project": service.extract_project_info(instance.project),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("epics.relateduserstory", "create")
@register_timeline_implementation("epics.relateduserstory", "change")
@register_timeline_implementation("epics.relateduserstory", "delete")
def epic_related_userstory_timeline(instance, extra_data={}):
    result = {
        "relateduserstory": service.extract_related_userstory_info(instance),
        "epic": service.extract_epic_info(instance.epic),
        "userstory": service.extract_userstory_info(instance.user_story, include_project=True),
        "project": service.extract_project_info(instance.project),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("userstories.userstory", "create")
@register_timeline_implementation("userstories.userstory", "change")
@register_timeline_implementation("userstories.userstory", "delete")
def userstory_timeline(instance, extra_data={}):
    result = {
        "userstory": service.extract_userstory_info(instance),
        "project": service.extract_project_info(instance.project),
    }

    if instance.milestone is not None:
        result["milestone"] = service.extract_milestone_info(instance.milestone)

    result.update(extra_data)
    return result


@register_timeline_implementation("issues.issue", "create")
@register_timeline_implementation("issues.issue", "change")
@register_timeline_implementation("issues.issue", "delete")
def issue_timeline(instance, extra_data={}):
    result = {
        "issue": service.extract_issue_info(instance),
        "project": service.extract_project_info(instance.project),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("tasks.task", "create")
@register_timeline_implementation("tasks.task", "change")
@register_timeline_implementation("tasks.task", "delete")
def task_timeline(instance, extra_data={}):
    result = {
        "task": service.extract_task_info(instance),
        "project": service.extract_project_info(instance.project),
    }

    if instance.user_story:
        result["task"]["userstory"] = service.extract_userstory_info(instance.user_story)

    result.update(extra_data)
    return result


@register_timeline_implementation("wiki.wikipage", "create")
@register_timeline_implementation("wiki.wikipage", "change")
@register_timeline_implementation("wiki.wikipage", "delete")
def wiki_page_timeline(instance, extra_data={}):
    result = {
        "wikipage": service.extract_wiki_page_info(instance),
        "project": service.extract_project_info(instance.project),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("projects.membership", "create")
@register_timeline_implementation("projects.membership", "delete")
def membership_timeline(instance, extra_data={}):
    result = {
        "user": service.extract_user_info(instance.user),
        "project": service.extract_project_info(instance.project),
        "role": service.extract_role_info(instance.role),
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("users.user", "create")
def user_timeline(instance, extra_data={}):
    result = {
        "user": service.extract_user_info(instance),
    }
    result.update(extra_data)
    return result
