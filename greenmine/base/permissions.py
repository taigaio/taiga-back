# -*- coding: utf-8 -*-

from __future__ import absolute_import

# FIXME: move this file to base.

from greenmine.profile.models import Role
from greenmine.scrum.models import ProjectUserRole


def get_role(name):
    """
    Helper method for a get role object
    finding by name.
    """
    return Role.objects.get(slug=name)


def has_perm(user, project, loc, perm, pur=None):
    """
    Checks if a user has a concrete permission on
    a project.
    """

    if not pur:
        try:
            pur = ProjectUserRole.objects.get(project=project, user=user)
        except ProjectUserRole.DoesNotExist:
            return False

    return getattr(pur.role, '%s_%s' % (loc.lower(), perm.lower()), False)


def has_perms(user, project, perms=[]):
    """
    Check a group of permissions in a single call.
    """

    if user.is_superuser:
        return True

    if project.owner == user:
        return True

    try:
        pur, valid = ProjectUserRole.objects\
            .get(project=project, user=user), True
    except ProjectUserRole.DoesNotExist:
        return False

    for pitem in perms:
        if len(pitem) != 2:
            continue

        loc, locperms = pitem
        if not isinstance(locperms, (list, tuple)):
            locperms = [locperms]

        valid = False not in [has_perm(user, project, loc, locperm, pur=pur)
                              for locperm in locperms]

        if not valid:
            break

    return valid
