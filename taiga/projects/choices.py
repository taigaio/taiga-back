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

from django.utils.translation import ugettext_lazy as _


VIDEOCONFERENCES_CHOICES = (
    ("appear-in", _("AppearIn")),
    ("jitsi", _("Jitsi")),
    ("custom", _("Custom")),
    ("talky", _("Talky")),
)

BLOCKED_BY_NONPAYMENT = "blocked-by-nonpayment"
BLOCKED_BY_STAFF = "blocked-by-staff"
BLOCKED_BY_OWNER_LEAVING = "blocked-by-owner-leaving"
BLOCKED_BY_DELETING = "blocked-by-deleting"

BLOCKING_CODES = [
    (BLOCKED_BY_NONPAYMENT, _("This project is blocked due to payment failure")),
    (BLOCKED_BY_STAFF, _("This project is blocked by admin staff")),
    (BLOCKED_BY_OWNER_LEAVING, _("This project is blocked because the owner left")),
    (BLOCKED_BY_DELETING, _("This project is blocked while it's deleted"))
]
