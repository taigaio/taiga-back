# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.utils.translation import gettext_lazy as _


VIDEOCONFERENCES_CHOICES = (
    ("whereby-com", _("Whereby.com")),
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
