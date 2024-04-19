# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.db.models import Q
from django.utils.translation import gettext as _
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


def check_if_project_privacy_can_be_changed(project):
    """Return if the project privacy can be changed from private to public or viceversa.

    :param project: A project object.

    :return: A dict like this {'can_be_updated': bool, 'reason': error message}.
    """
    if project.owner is None:
        return {'can_be_updated': False, 'reason': ERROR_PROJECT_WITHOUT_OWNER}

    current_projects = (project.owner.owned_projects.filter(is_private=not project.is_private)
                                                    .count())
    Membership = apps.get_model("projects", "Membership")
    current_memberships = (Membership.objects.filter(Q(project__is_private=not project.is_private,  # public/private members
                                                       project__owner_id=project.owner_id,
                                                       user_id__isnull=False) |
                                                     Q(project_id=project.pk,  # current project members
                                                       user_id__isnull=False))
                                             .values("user_id")
                                             .distinct()
                                             .count()) # Just confirmed members

    current_memberships += (Membership.objects.filter(Q(project__is_private=not project.is_private,  # public/private members
                                                        project__owner_id=project.owner_id,
                                                        user_id__isnull=True) |
                                                      Q(project_id=project.pk,  # current project members
                                                        user_id__isnull=True))
                                              .values("email")
                                              .distinct()
                                              .count()) # Just pending members

    if project.is_private:
        max_projects = project.owner.max_public_projects
        max_memberships = project.owner.max_memberships_public_projects
        error_project_exceeded = ERROR_MAX_PUBLIC_PROJECTS
        error_memberships_exceeded = ERROR_MAX_PUBLIC_PROJECTS_MEMBERSHIPS
    else:
        max_projects = project.owner.max_private_projects
        max_memberships = project.owner.max_memberships_private_projects
        error_project_exceeded = ERROR_MAX_PRIVATE_PROJECTS
        error_memberships_exceeded = ERROR_MAX_PRIVATE_PROJECTS_MEMBERSHIPS

    if max_memberships is not None and current_memberships > max_memberships:
        return {'can_be_updated': False, 'reason': error_memberships_exceeded}

    if max_projects is not None and current_projects >= max_projects:
        return {'can_be_updated': False, 'reason': error_project_exceeded}

    return {'can_be_updated': True, 'reason': None}


def check_if_project_can_be_created_or_updated(project):
    """Return if the project can be create or update (the privacy).

    :param project: A project object.

    :return: (bool, error_mesage, int) return a tuple (can be duplicated, error message, total new project members).
    """
    if project.owner is None:
        return (False, ERROR_PROJECT_WITHOUT_OWNER, 0)

    current_projects = project.owner.owned_projects.filter(is_private=project.is_private).count()
    Membership = apps.get_model("projects", "Membership")
    current_memberships = (Membership.objects.filter(project__is_private=project.is_private,
                                                     project__owner_id=project.owner_id,
                                                     user_id__isnull=False)
                                             .values("user_id")
                                             .distinct()
                                             .count()) # Just confirmed members
    current_memberships += (Membership.objects.filter(project__is_private=project.is_private,
                                                      project__owner_id=project.owner_id,
                                                      user_id__isnull=True)
                                              .values("email")
                                              .distinct()
                                              .count()) # Pending members

    if project.is_private:
        max_projects = project.owner.max_private_projects
        max_memberships = project.owner.max_memberships_private_projects
        error_project_exceeded = _("You can't have more private projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        max_projects = project.owner.max_public_projects
        max_memberships = project.owner.max_memberships_public_projects
        error_project_exceeded = _("You can't have more public projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded, current_memberships)

    if max_memberships is not None and current_memberships > max_memberships:
        return (False, error_memberships_exceeded, current_memberships)

    return (True, None, current_memberships)


def check_if_project_can_be_transfered(project, new_owner):
    """Return if the project can be transfered to another member.

    :param project: A project object.
    :param new_owner: The new owner.

    :return: (bool, error_mesage, int) return a tuple (can be duplicated, error message, total new project members).
    """
    if project.owner == new_owner:
        return (True, None, 0)

    current_projects = new_owner.owned_projects.filter(is_private=project.is_private).count()
    Membership = apps.get_model("projects", "Membership")
    current_memberships = (Membership.objects.filter(Q(project__is_private=project.is_private,  # public/private members
                                                       project__owner_id=new_owner.id,
                                                       user_id__isnull=False) |
                                                     Q(project_id=project.pk,  # current project members
                                                       user_id__isnull=False))
                                             .values("user_id")
                                             .distinct()
                                             .count())  # Just confirmed members
    current_memberships += (Membership.objects.filter(Q(project__is_private=project.is_private,  # public/private members
                                                        project__owner_id=new_owner.id,
                                                        user_id__isnull=True) |
                                                      Q(project_id=project.pk,  # current project members
                                                        user_id__isnull=True))
                                             .values("email")
                                             .distinct()
                                             .count())  # Pending members

    if project.is_private:
        max_projects = new_owner.max_private_projects
        max_memberships = new_owner.max_memberships_private_projects
        error_project_exceeded = _("You can't have more private projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        max_projects = new_owner.max_public_projects
        max_memberships = new_owner.max_memberships_public_projects
        error_project_exceeded = _("You can't have more public projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded, current_memberships)

    if max_memberships is not None and current_memberships > max_memberships:
        return (False, error_memberships_exceeded, current_memberships)

    return (True, None, current_memberships)


def check_if_project_can_be_duplicate(project, new_owner, new_is_private, new_user_id_members):
    """Return if the project can be duplicate.

    :param project: A project object.
    :param new_owner: The new owner.
    :param new_is_private: 'True' if new project will be private.
    :param new_user_id_members: A list of user ids for new members.

    :return: (bool, error_mesage, int) return a tuple (can be duplicated, error message, total new project members).
    """
    current_projects = new_owner.owned_projects.filter(is_private=project.is_private).count()
    Membership = apps.get_model("projects", "Membership")
    actual_user_id_members = (Membership.objects.filter(project__is_private=new_is_private,
                                                        project__owner_id=new_owner.id,
                                                        user_id__isnull=False)
                                                .values("user_id")
                                                .distinct()
                                                .values_list("user__id", flat=True))
    total_pending_members = (Membership.objects.filter(project__is_private=new_is_private,
                                                       project__owner_id=new_owner.id,
                                                       user_id__isnull=True)
                                               .values("email")
                                               .distinct()
                                               .count())

    current_memberships = len(
        set(list(actual_user_id_members) + new_user_id_members)
        - set([new_owner.id]) # remove owner if exist, maybe not
    )
    current_memberships += 1  # +1 for new owner
    current_memberships += total_pending_members

    if new_is_private:
        max_projects = new_owner.max_private_projects
        max_memberships = new_owner.max_memberships_private_projects
        error_project_exceeded = _("You can't have more private projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for private projects")
    else:
        max_projects = new_owner.max_public_projects
        max_memberships = new_owner.max_memberships_public_projects
        error_project_exceeded = _("You can't have more public projects")
        error_memberships_exceeded = _("This project reaches your current limit of memberships for public projects")

    if max_projects is not None and current_projects >= max_projects:
        return (False, error_project_exceeded, current_memberships)

    if max_memberships is not None and current_memberships > max_memberships:
        return (False, error_memberships_exceeded, current_memberships)

    return (True, None, current_memberships)


def check_if_project_is_out_of_owner_limits(project):
    """Return if the project fits on its owner limits.

    :param project: A project object.

    :return: bool
    """
    if project.owner is None:
        return False

    current_projects = project.owner.owned_projects.filter(is_private=project.is_private).count()
    Membership = apps.get_model("projects", "Membership")
    current_memberships = (Membership.objects.filter(project__is_private=project.is_private,
                                                     project__owner_id=project.owner_id,
                                                     user_id__isnull=False)
                                             .values("user_id")
                                             .distinct()
                                             .count()) # Current confirmed members
    current_memberships += (Membership.objects.filter(project__is_private=project.is_private,
                                                      project__owner_id=project.owner_id,
                                                      user_id__isnull=True)
                                              .values("email")
                                              .distinct()
                                              .count()) # Pending members

    if project.is_private:
        max_projects = project.owner.max_private_projects
        max_memberships = project.owner.max_memberships_private_projects
    else:
        max_projects = project.owner.max_public_projects
        max_memberships = project.owner.max_memberships_public_projects

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
