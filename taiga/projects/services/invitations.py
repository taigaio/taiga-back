# -*- coding: utf-8 -*-
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

from django.apps import apps
from django.conf import settings

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

    :param invitation: Invitation object.
    :param default: Default object to return if user is not found.

    TODO: only used by importer/exporter and should be moved here

    :return: The user if it's found, othwerwise return `default`.
    """

    User = apps.get_model(settings.AUTH_USER_MODEL)

    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return default
