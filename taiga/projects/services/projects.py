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

from django.apps import apps
from django.utils.translation import ugettext as _
from taiga.celery import app
from taiga.base.api.utils import get_object_or_404
from taiga.permissions import services as permissions_services
from taiga.projects.history.services import take_snapshot

from .. import choices
from ..apps import connect_projects_signals, disconnect_projects_signals

ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS = 'max_public_projects_memberships'
ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS = 'max_private_projects_memberships'
ERROR_MAX_PUBLIC_PROJECTS = 'max_public_projects'
ERROR_MAX_PRIVATE_PROJECTS = 'max_private_projects'
ERROR_PROJECT_WITHOUT_OWNER = 'project_without_owner'


def check_if_project_privacity_can_be_changed(
        project,
        current_memberships=None,
        current_private_projects=None,
        current_public_projects=None):
    """Return if the project privacity can be changed from private to public or viceversa.

    :param project: A project object.
    :param current_memberships: Project total memberships, If None it will be calculated.
    :param current_private_projects: total private projects owned by the project owner, If None it will be calculated.
    :param current_public_projects: total public projects owned by the project owner, If None it will be calculated.

    :return: A dict like this {'can_be_updated': bool, 'reason': error message}.
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if current_memberships is None:
        current_memberships = project.memberships.count()

    if project.is_private:
        max_memberships = project.owner.max_memberships_public_projects
        error_memberships_exceeded = ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS

        if current_public_projects is None:
            current_projects = project.owner.owned_projects.filter(is_private=False).count()
        else:
            current_projects = current_public_projects

        max_projects = project.owner.max_public_projects
        error_project_exceeded = ERROR_MAX_PUBLIC_PROJECTS
    else:
        max_memberships = project.owner.max_memberships_private_projects
        error_memberships_exceeded = ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS

        if current_private_projects is None:
            current_projects = project.owner.owned_projects.filter(is_private=True).count()
        else:
            current_projects = current_private_projects

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
        error_project_exceeded = _("You can't have more private projects")

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
        error_project_exceeded = _("You can't have more private projects")

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


def check_if_project_is_out_of_owner_limits(
        project,
        current_memberships=None,
        current_private_projects=None,
        current_public_projects=None):

    """Return if the project fits on its owner limits.

    :param project: A project object.
    :param current_memberships: Project total memberships, If None it will be calculated.
    :param current_private_projects: total private projects owned by the project owner, If None it will be calculated.
    :param current_public_projects: total public projects owned by the project owner, If None it will be calculated.

    :return: bool
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    if current_memberships is None:
        current_memberships = project.memberships.count()

    if project.is_private:
        max_memberships = project.owner.max_memberships_private_projects

        if current_private_projects is None:
            current_projects = project.owner.owned_projects.filter(is_private=True).count()
        else:
            current_projects = current_private_projects

        max_projects = project.owner.max_private_projects
    else:
        max_memberships = project.owner.max_memberships_public_projects

        if current_public_projects is None:
            current_projects = project.owner.owned_projects.filter(is_private=False).count()
        else:
            current_projects = current_public_projects

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


@app.task
def delete_projects(projects):
    for project in projects:
        delete_project(project.id)


def duplicate_project(project, **new_project_extra_args):
    owner = new_project_extra_args.get("owner")
    users = new_project_extra_args.pop("users")

    disconnect_projects_signals()
    Project = apps.get_model("projects", "Project")
    new_project = Project.objects.create(**new_project_extra_args)
    connect_projects_signals()

    permissions_services.set_base_permissions_for_project(new_project)

    # Cloning the structure from the old project using templates
    Template = apps.get_model("projects", "ProjectTemplate")
    template = Template()
    template.load_data_from_project(project)
    template.apply_to_project(new_project)
    new_project.creation_template = project.creation_template
    new_project.save()

    # Creating the membership for the new owner
    Membership = apps.get_model("projects", "Membership")
    Membership.objects.create(
        user=owner,
        is_admin=True,
        role=new_project.roles.get(slug=template.default_owner_role),
        project=new_project
    )

    # Creating the extra memberships
    for user in users:
        project_memberships = project.memberships.exclude(user_id=owner.id)
        membership = get_object_or_404(project_memberships, user_id=user["id"])
        Membership.objects.create(
            user=membership.user,
            is_admin=membership.is_admin,
            role=new_project.roles.get(slug=membership.role.slug),
            project=new_project
        )

    # Take initial snapshot for the project
    take_snapshot(new_project, user=owner)
    return new_project
