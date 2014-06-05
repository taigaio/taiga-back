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
def project_create_timeline(instance, extra_data={}):
    return {
        "project": {
            "id": instance.pk,
            "slug": instance.slug,
            "name": instance.name,
        },
        "creator": {
            "id": instance.owner.pk,
            "name": instance.owner.get_full_name(),
        }
    }


@register_timeline_implementation("userstories.userstory", "create")
def userstory_create_timeline(instance, extra_data={}):
    return {
        "userstory": {
            "id": instance.pk,
            "subject": instance.subject,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        },
        "creator": {
            "id": instance.owner.pk,
            "name": instance.owner.get_full_name(),
        }
    }


@register_timeline_implementation("issues.issue", "create")
def issue_create_timeline(instance, extra_data={}):
    return {
        "issue": {
            "id": instance.pk,
            "subject": instance.subject,
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        },
        "creator": {
            "id": instance.owner.pk,
            "name": instance.owner.get_full_name(),
        }
    }


@register_timeline_implementation("projects.membership", "create")
def membership_create_timeline(instance, extra_data={}):
    return {
        "user": {
            "id": instance.user.pk,
            "name": instance.user.get_full_name(),
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        },
        "role": {
            "id": instance.role.pk,
            "name": instance.role.name,
        }
    }


@register_timeline_implementation("projects.membership", "delete")
def membership_delete_timeline(instance, extra_data={}):
    return {
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


@register_timeline_implementation("projects.membership", "role-changed")
def membership_role_changed_timeline(instance, extra_data={}):
    result = {
        "user": {
            "id": instance.user.pk,
            "name": instance.user.get_full_name(),
        },
        "project": {
            "id": instance.project.pk,
            "slug": instance.project.slug,
            "name": instance.project.name,
        },
        "role": {
            "id": instance.role.pk,
            "name": instance.role.name,
        }
    }
    return dict(result.items() + extra_data.items())
