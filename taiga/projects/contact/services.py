# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.mails import mail_builder
from taiga.celery import app
from taiga.front.templatetags.functions import resolve as resolve_front_url
from taiga.users.services import get_user_photo_url

from . import models


@app.task
def send_contact_email(contact_entry_id):
    contact_entry = models.ContactEntry.objects.filter(id=contact_entry_id).first()
    if contact_entry is None:
        return

    ctx = {
        "comment": contact_entry.comment,
        "full_name": contact_entry.user.get_full_name(),
        "project_name": contact_entry.project.name,
        "photo_url": get_user_photo_url(contact_entry.user),
        "user_profile_url": resolve_front_url("user", contact_entry.user.username),
        "project_settings_url": resolve_front_url("project-admin", contact_entry.project.slug),
    }
    admins = contact_entry.project.get_users(with_admin_privileges=True).exclude(id=contact_entry.user_id)
    for admin in admins:
        email = mail_builder.contact_notification(admin.email, ctx)
        email.extra_headers["Reply-To"] = contact_entry.user.email
        email.send()
