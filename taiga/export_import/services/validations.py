# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.utils.translation import gettext as _


def has_available_slot_for_new_project(owner, is_private, member_emails):
    """Return if user has enought slots to create a new projects.

    :param owner: The new owner.
    :param is_private: 'True' if new project will be private.
    :param member_emails: A list of user ids for new members.

    :return: (bool, error_mesage, int) return a tuple (can be duplicated, error message, total new project members).
    """
    current_projects = owner.owned_projects.filter(is_private=is_private).count()
    Membership = apps.get_model("projects", "Membership")
    actual_emails_members = (Membership.objects.filter(project__is_private=is_private,
                                                       project__owner_id=owner.id,
                                                       user_id__isnull=False)
                                                .order_by("user__email")
                                                .distinct("user__email")
                                                .values_list("user__email", flat=True))

    total_memberships = len(set(list(actual_emails_members) + member_emails) - set([owner.email])) + 1

    if is_private:
        max_projects = owner.max_private_projects
        max_memberships = owner.max_memberships_private_projects
        error_project_exceeded =  _("You can't have more private projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        max_projects = owner.max_public_projects
        max_memberships = owner.max_memberships_public_projects
        error_project_exceeded = _("You can't have more public projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded, total_memberships)

    if max_memberships is not None and total_memberships > max_memberships:
        return (False, error_memberships_exceeded, total_memberships)

    return (True, None, total_memberships)
