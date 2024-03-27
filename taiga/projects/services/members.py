# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import uuid

from taiga.base.exceptions import ValidationError, WrongArguments
from taiga.base.utils import db
from taiga.users.models import User
from taiga.users.services import get_user_by_username_or_email

from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import gettext as _

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

        # Try to find the user
        username = data_copy.pop("username")
        try:
            user = get_user_by_username_or_email(username)
            data_copy["user_id"] = user.id
        except WrongArguments:
            # If not exist, is an invitation. Set the email and a token
            try:
                validate_email(username)
                data_copy["email"] = username
            except ValidationError:
                raise WrongArguments(_("Malformed email adress."))

            if "token" not in data_copy.keys():
                data_copy["token"] = str(uuid.uuid1())

        data_copy.update(additional_fields)

        members.append(models.Membership(**data_copy))

    return members


def create_members_in_bulk(members, callback=None, precall=None):
    """Create members from `bulk_data`.

    :param members: List of dicts `{"project_id": <>, "role_id": <>, "username": <>}`.
    :param callback: Callback to execute after each task save.
    :param additional_fields: Additional fields when instantiating each task.

    """
    db.save_in_bulk(members, callback, precall)


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

    # The user can't leave if is the real owner of the project
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
    if project.owner is None:
        return None

    if project.is_private:
        return project.owner.max_memberships_private_projects
    return project.owner.max_memberships_public_projects


def get_total_project_memberships(project):
    """Return tha total of memberships of a project (members and unaccepted invitations).

    :param project: A project object.

    :return: a number.
    """
    return project.memberships.count()


def check_if_new_member_can_be_created(new_membership):
    """Return if a new mebership could be created.

    :param new_memberships: the new membershhip object (not saved in the database jet)

    :return: {bool, error_mesage, total_memberships} return a tuple (can add new members?, error message, total of members).
    """
    project = new_membership.project

    if project.owner is None:
        return False, _("Project without owner"), None

    confirmed_memberships = (models.Membership.objects.filter(project__is_private=project.is_private,
                                                              project__owner_id=project.owner_id,
                                                              user_id__isnull=False)
                                                      .order_by("user_id")
                                                      .distinct("user_id")
                                                      .count()) # Just confirmed members
    pending_memberships = (models.Membership.objects.filter(project__is_private=project.is_private,
                                                            project__owner_id=project.owner_id,
                                                            user_id__isnull=True)
                                                     .order_by("email")
                                                     .distinct("email")
                                                     .count()) # Pending members
    if new_membership.user_id:
        confirmed_memberships +=1
    else:
        pending_memberships +=1

    total_memberships = confirmed_memberships + pending_memberships

    if project.is_private:
        max_memberships = project.owner.max_memberships_private_projects
        error_members_exceeded = _("You have reached your current limit of memberships for private projects")
    else:
        max_memberships = project.owner.max_memberships_public_projects
        error_members_exceeded = _("You have reached your current limit of memberships for public projects")

    if max_memberships is not None and total_memberships > max_memberships:
        return False, error_members_exceeded, total_memberships

    if not new_membership.user_id and project.memberships.filter(user=None).count() + 1 > settings.MAX_PENDING_MEMBERSHIPS:
        error_pending_memberships_exceeded = _("You have reached the current limit of pending memberships")
        return False, error_pending_memberships_exceeded, pending_memberships

    return True, None, total_memberships


def check_if_new_members_can_be_created(project, new_memberships):
    """Return if some new meberships could be created.

    :param project: the common projects for all the memberships
    :param new_memberships: a list with the new membershhips object (not saved in the database jet)

    :return: {bool, error_mesage, total_memberships} return a tuple (can add new members?, error message, total of members).
    """
    if project.owner is None:
        return False, _("Project without owner"), None

    new_confirmed_memberships = [m.user_id for m in new_memberships if m.user_id]
    new_pending_memberships = [m.email for m in new_memberships if not m.user_id]

    confirmed_memberships = (models.Membership.objects.filter(project__is_private=project.is_private,
                                                              project__owner_id=project.owner_id,
                                                              user_id__isnull=False)
                                                      .order_by("user_id")
                                                      .distinct("user_id")
                                                      .values_list("user_id", flat=True)) # Just confirmed members
    pending_memberships = (models.Membership.objects.filter(project__is_private=project.is_private,
                                                            project__owner_id=project.owner_id,
                                                            user_id__isnull=True)
                                                     .order_by("email")
                                                     .distinct("email")
                                                     .values_list("email", flat=True))

    total_memberships =  len({*pending_memberships, *new_pending_memberships, *confirmed_memberships, *new_confirmed_memberships})
    total_pending_memberships = len({*pending_memberships, *new_pending_memberships})

    if project.is_private:
        max_memberships = project.owner.max_memberships_private_projects
        error_members_exceeded = _("You have reached your current limit of memberships for private projects")
    else:
        max_memberships = project.owner.max_memberships_public_projects
        error_members_exceeded = _("You have reached your current limit of memberships for public projects")

    if max_memberships is not None and total_memberships > max_memberships:
        return False, error_members_exceeded, total_memberships

    if new_pending_memberships and project.memberships.filter(user=None).count() + len(new_pending_memberships) > settings.MAX_PENDING_MEMBERSHIPS:
        error_pending_memberships_exceeded = _("You have reached the current limit of pending memberships")
        return False, error_pending_memberships_exceeded, pending_memberships

    return True, None, total_memberships
