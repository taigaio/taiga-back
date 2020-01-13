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
