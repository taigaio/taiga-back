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

from taiga.timeline.service import register_timeline_implementation


@register_timeline_implementation("projects.project", "create")
@register_timeline_implementation("projects.project", "change")
@register_timeline_implementation("projects.project", "delete")
def project_timeline(instance, extra_data={}):
    result ={
        "project": {
            "id": instance.pk,
            "slug": instance.slug,
            "name": instance.name,
        },
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("milestones.milestone", "create")
@register_timeline_implementation("milestones.milestone", "change")
@register_timeline_implementation("milestones.milestone", "delete")
def project_timeline(instance, extra_data={}):
    result ={
        "milestone": {
            "id": instance.pk,
            "slug": instance.slug,
            "name": instance.name,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        }
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("userstories.userstory", "create")
@register_timeline_implementation("userstories.userstory", "change")
@register_timeline_implementation("userstories.userstory", "delete")
def userstory_timeline(instance, extra_data={}):
    result ={
        "userstory": {
            "id": instance.pk,
            "subject": instance.subject,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        }
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("issues.issue", "create")
@register_timeline_implementation("issues.issue", "change")
@register_timeline_implementation("issues.issue", "delete")
def issue_timeline(instance, extra_data={}):
    result ={
        "issue": {
            "id": instance.pk,
            "subject": instance.subject,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        }
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("tasks.task", "create")
@register_timeline_implementation("tasks.task", "change")
@register_timeline_implementation("tasks.task", "delete")
def task_timeline(instance, extra_data={}):
    result ={
        "task": {
            "id": instance.pk,
            "subject": instance.subject,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        }
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("wiki.wikipage", "create")
@register_timeline_implementation("wiki.wikipage", "change")
@register_timeline_implementation("wiki.wikipage", "delete")
def wiki_page_timeline(instance, extra_data={}):
    result ={
        "wiki_page": {
            "id": instance.pk,
            "slug": instance.slug,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        }
    }
    result.update(extra_data)
    return result


@register_timeline_implementation("projects.membership", "create")
@register_timeline_implementation("projects.membership", "delete")
def membership_create_timeline(instance, extra_data={}):
    result =  {
        "user": {
            "id": instance.user.pk,
            "name": instance.user.get_full_name(),
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        },
    }
    result.update(extra_data)
    return result
