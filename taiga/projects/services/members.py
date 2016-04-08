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


def check_if_project_can_have_more_memberships(project, total_new_memberships):
    """Return if a project can have more n new memberships.

    :param project: A project object.
    :param total_new_memberships: the total of new memberships to add (int).

    :return: {bool, error_mesage} return a tuple (can add new members?, error message).
    """
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
