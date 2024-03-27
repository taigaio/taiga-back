# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction as tx
from django.db import IntegrityError
from django.utils.translation import gettext as _

from taiga.base import exceptions as exc

from taiga.base.mails import mail_builder


def send_invitation(invitation):
    """Send an invitation email"""
    if invitation.user:
        template = mail_builder.membership_notification
        email = template(invitation.user, {"membership": invitation})
    else:
        template = mail_builder.membership_invitation
        email = template(invitation.email, {"membership": invitation})

    email.send()


def find_invited_user(email, default=None):
    """Check if the invited user is already a registered.

    :param email: some user email
    :param default: Default object to return if user is not found.

    :return: The user if it's found, othwerwise return `default`.
    """

    User = apps.get_model(settings.AUTH_USER_MODEL)
    qs = User.objects.filter(email__iexact=email)

    if len(qs) > 1:
        qs = qs.filter(email=email)

    if len(qs) == 0:
        return default

    return qs[0]


def get_membership_by_token(token:str):
    """
    Given an invitation token, returns a membership instance
    that matches with specified token.

    If not matches with any membership NotFound exception
    is raised.
    """
    membership_model = apps.get_model("projects", "Membership")
    qs = membership_model.objects.filter(token=token)
    if len(qs) == 0:
        raise exc.NotFound(_("Token does not match any valid invitation."))
    return qs[0]


@tx.atomic
def accept_invitation_by_existing_user(token:str, user_id:int):
    user_model = get_user_model()
    try:
        user = user_model.objects.get(id=user_id)
    except user_model.DoesNotExist:
        raise exc.NotFound(_("User does not exist."))

    membership = get_membership_by_token(token)
    try:
        membership.user = user
        membership.save(update_fields=["user"])
    except IntegrityError:
        raise exc.IntegrityError(_("This user is already a member of the project."))
    return user
