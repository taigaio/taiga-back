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

from django.apps import apps
from django.utils.translation import ugettext as _
from taiga.celery import app
from .. import choices

ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS = 'max_public_projects_memberships'
ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS = 'max_private_projects_memberships'
ERROR_MAX_PUBLIC_PROJECTS = 'max_public_projects'
ERROR_MAX_PRIVATE_PROJECTS = 'max_private_projects'
ERROR_PROJECT_WITHOUT_OWNER = 'project_without_owner'

def check_if_project_privacity_can_be_changed(project):
    """Return if the project privacity can be changed from private to public or viceversa.

    :param project: A project object.

    :return: A dict like this {'can_be_updated': bool, 'reason': error message}.
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if project.is_private:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_public_projects
        error_memberships_exceeded = ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS

        current_projects = project.owner.owned_projects.filter(is_private=False).count()
        max_projects = project.owner.max_public_projects
        error_project_exceeded = ERROR_MAX_PUBLIC_PROJECTS
    else:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_private_projects
        error_memberships_exceeded = ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS

        current_projects = project.owner.owned_projects.filter(is_private=True).count()
        max_projects = project.owner.max_private_projects
        error_project_exceeded = ERROR_MAX_PRIVATE_PROJECTS

    if max_memberships is not None and current_memberships > max_memberships:
        return {'can_be_updated': False, 'reason': error_memberships_exceeded}

    if max_projects is not None and current_projects >= max_projects:
        return {'can_be_updated': False, 'reason': error_project_exceeded}

    return {'can_be_updated': True, 'reason': None}


def check_if_project_can_be_created_or_updated(project):
    """Return if the project can be create or update (the privacity).

    :param project: A project object.

    :return: {bool, error_mesage} return a tuple (can be created or updated, error message).
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if project.is_private:
        current_projects = project.owner.owned_projects.filter(is_private=True).count()
        max_projects = project.owner.max_private_projects
        error_project_exceeded =  _("You can't have more private projects")

        current_memberships = project.memberships.count() or 1
        max_memberships = project.owner.max_memberships_private_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        current_projects = project.owner.owned_projects.filter(is_private=False).count()
        max_projects = project.owner.max_public_projects
        error_project_exceeded = _("You can't have more public projects")

        current_memberships = project.memberships.count() or 1
        max_memberships = project.owner.max_memberships_public_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded)

    if max_memberships is not None and current_memberships > max_memberships:
        return (False, error_memberships_exceeded)

    return (True, None)


def check_if_project_can_be_transfered(project, new_owner):
    """Return if the project can be transfered to another member.

    :param project: A project object.
    :param new_owner: The new owner.

    :return: {bool, error_mesage} return a tuple (can be transfered?, error message).
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if project.owner == new_owner:
        return (True, None)

    if project.is_private:
        current_projects = new_owner.owned_projects.filter(is_private=True).count()
        max_projects = new_owner.max_private_projects
        error_project_exceeded =  _("You can't have more private projects")

        current_memberships = project.memberships.count()
        max_memberships = new_owner.max_memberships_private_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        current_projects = new_owner.owned_projects.filter(is_private=False).count()
        max_projects = new_owner.max_public_projects
        error_project_exceeded = _("You can't have more public projects")

        current_memberships = project.memberships.count()
        max_memberships = new_owner.max_memberships_public_projects
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded)

    if max_memberships is not None and current_memberships > max_memberships:
        return (False, error_memberships_exceeded)

    return (True, None)


def check_if_project_is_out_of_owner_limits(project):
    """Return if the project fits on its owner limits.

    :param project: A project object.

    :return: bool
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if project.is_private:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_private_projects
        current_projects = project.owner.owned_projects.filter(is_private=True).count()
        max_projects = project.owner.max_private_projects
    else:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_public_projects
        current_projects = project.owner.owned_projects.filter(is_private=False).count()
        max_projects = project.owner.max_public_projects

    if max_memberships is not None and current_memberships > max_memberships:
        return True

    if max_projects is not None and current_projects > max_projects:
        return True

    return False


def orphan_project(project):
    project.memberships.filter(user=project.owner).delete()
    project.owner = None
    project.blocked_code = choices.BLOCKED_BY_DELETING
    project.save()


@app.task
def delete_project(project_id):
    Project = apps.get_model("projects", "Project")
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return

    project.delete_related_content()
    project.delete()
