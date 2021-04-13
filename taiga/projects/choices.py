# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _


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
