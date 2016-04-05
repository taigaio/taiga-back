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

from taiga.base.utils import db, text
from django.utils.translation import ugettext as _

from .. import models

def get_members_from_bulk(bulk_data, **additional_fields):
    """Convert `bulk_data` into a list of members.

    :param bulk_data: List of members in bulk format.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of `Member` instances.
    """
    members = []
    for data in bulk_data:
        data_copy = data.copy()
        data_copy.update(additional_fields)
        members.append(models.Membership(**data_copy))
    return members


def create_members_in_bulk(bulk_data, callback=None, precall=None, **additional_fields):
    """Create members from `bulk_data`.

    :param bulk_data: List of dicts `{"project_id": <>, "role_id": <>, "email": <>}`.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    :return: List of created `Member` instances.
    """
    members = get_members_from_bulk(bulk_data, **additional_fields)
    db.save_in_bulk(members, callback, precall)
    return members


def remove_user_from_project(user, project):
    models.Membership.objects.get(project=project, user=user).delete()


def project_has_valid_admins(project, exclude_user=None):
    """
    Checks if the project has any owner membership with a user different than the specified
    """
    admin_memberships = project.memberships.filter(is_admin=True, user__is_active=True)
    if exclude_user:
        admin_memberships = admin_memberships.exclude(user=exclude_user)

    return admin_memberships.count() > 0


def can_user_leave_project(user, project):
    membership = project.memberships.get(user=user)
    if not membership.is_admin:
         return True

    #The user can't leave if is the real owner of the project
    if project.owner == user:
        return False

    if not project_has_valid_admins(project, exclude_user=user):
        return False

    return True


def get_max_memberships_for_project(project):
    """Return tha maximun of membersh for a concrete project.

    :param project: A project object.

    :return: a number or null.
    """
    if project.is_private:
        return project.owner.max_memberships_private_projects
    return project.owner.max_memberships_public_projects


def get_total_project_memberships(project):
    """Return tha total of memberships of a project (members and unaccepted invitations).

    :param project: A project object.

    :return: a number.
    """
    return project.memberships.count()


ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS = 'max_public_projects_memberships'
ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS = 'max_private_projects_memberships'
ERROR_MAX_PUBLIC_PROJECTS = 'max_public_projects'
ERROR_MAX_PRIVATE_PROJECTS = 'max_private_projects'

def check_if_project_privacity_can_be_changed(project):
    """Return if the project privacity can be changed from private to public or viceversa.

    :param project: A project object.

    :return: True if it can be changed or False if can't.
    """
    if project.is_private:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_public_projects
        error_members_exceeded = ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS

        current_projects = project.owner.owned_projects.filter(is_private=False).count()
        max_projects = project.owner.max_public_projects
        error_project_exceeded = ERROR_MAX_PUBLIC_PROJECTS
    else:
        current_memberships = project.memberships.count()
        max_memberships = project.owner.max_memberships_private_projects
        error_members_exceeded = ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS

        current_projects = project.owner.owned_projects.filter(is_private=True).count()
        max_projects = project.owner.max_private_projects
        error_project_exceeded = ERROR_MAX_PRIVATE_PROJECTS

    if max_memberships is not None and current_memberships > max_memberships:
        return {'can_be_updated': False, 'reason': error_members_exceeded}

    if max_projects is not None and current_projects >= max_projects:
        return {'can_be_updated': False, 'reason': error_project_exceeded}

    return {'can_be_updated': True, 'reason': None}


def check_if_project_can_have_more_memberships(project, total_new_memberships):
    if project.is_private:
        total_memberships = project.memberships.count() + total_new_memberships
        max_memberships = project.owner.max_memberships_private_projects
        error_members_exceeded = _("You have reached your current limit of memberships for private projects")
    else:
        total_memberships = project.memberships.count() + total_new_memberships
        max_memberships = project.owner.max_memberships_public_projects
        error_members_exceeded = _("You have reached your current limit of memberships for public projects")

    if max_memberships is not None and total_memberships > max_memberships:
        return False, error_members_exceeded

    return True, None
