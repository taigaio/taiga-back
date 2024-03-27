# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core import signing
from django.utils.translation import gettext as _

import datetime

from taiga.base.mails import mail_builder
from taiga.base import exceptions as exc


def request_project_transfer(project, user):
    template = mail_builder.transfer_request
    email = template(project.owner, {"project": project, "requester": user})
    email.send()


def start_project_transfer(project, user, reason):
    """Generates the transfer token for a project transfer and notify to the destination user

    :param project: Project trying to transfer
    :param user: Destination user
    :param reason: Reason to transfer the project
    """

    signer = signing.TimestampSigner()
    token = signer.sign(user.id)
    project.transfer_token = token
    project.save()

    template = mail_builder.transfer_start
    context = {
        "project": project,
        "receiver": user,
        "token": token,
        "reason": reason
    }
    email = template(user, context)
    email.send()


def validate_project_transfer_token(token, project, user):
    signer = signing.TimestampSigner()

    if project.transfer_token != token:
        raise exc.WrongArguments(_("Token is invalid"))

    try:
        value = signer.unsign(token, max_age=datetime.timedelta(days=7))
    except signing.SignatureExpired:
        raise exc.WrongArguments(_("Token has expired"))
    except signing.BadSignature:
        raise exc.WrongArguments(_("Token is invalid"))

    if str(value) != str(user.id):
        raise exc.WrongArguments(_("Token is invalid"))


def reject_project_transfer(project, user, token, reason):
    validate_project_transfer_token(token, project, user)

    project.transfer_token = None
    project.save()

    template = mail_builder.transfer_reject
    context = {
        "project": project,
        "rejecter": user,
        "reason": reason
    }
    email = template(project.owner, context)
    email.send()


def accept_project_transfer(project, user, token, reason):
    validate_project_transfer_token(token, project, user)

    # Set new owner as project admin
    membership = project.memberships.get(user=user)
    if not membership.is_admin:
        membership.is_admin = True
        membership.save()

    # Change the owner of the project
    old_owner = project.owner
    project.transfer_token = None
    project.owner = user
    project.save()

    # Send mail
    template = mail_builder.transfer_accept
    context = {
        "project": project,
        "old_owner": old_owner,
        "new_owner": user,
        "reason": reason
    }
    email = template(old_owner, context)
    email.send()
