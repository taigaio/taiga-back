# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _


US_STATUSES = (
    (1, _("Open"), False, True),
    (2, _("Closed"), True, False),
)

TASK_STATUSES = (
    (1, _("New"), False, True,  "#999999"),
    (2, _("In progress"), False, False, "#ff9900"),
    (3, _("Ready for test"), True, False, "#ffcc00"),
    (4, _("Closed"), True, False, "#669900"),
    (5, _("Needs Info"), False, False, "#999999"),
)

POINTS_CHOICES = (
    (1, u'?', None, True),
    (2,  u'0', 0, False),
    (3, u'1/2', 0.5, False),
    (4,  u'1', 1, False),
    (5,  u'2', 2, False),
    (6,  u'3', 3, False),
    (7,  u'5', 5, False),
    (8,  u'8', 8, False),
    (9, u'10', 10, False),
    (10, u'15', 15, False),
    (11, u'20', 20, False),
    (12, u'40', 40, False),
)

PRIORITY_CHOICES = (
    (1, _(u'Low'), '#666666', False),
    (3, _(u'Normal'), '#669933', True),
    (5, _(u'High'), '#CC0000', False),
)

SEVERITY_CHOICES = (
    (1, _(u'Wishlist'), '#666666', False),
    (2, _(u'Minor'), '#669933', False),
    (3, _(u'Normal'), 'blue', True),
    (4, _(u'Important'), 'orange', False),
    (5, _(u'Critical'), '#CC0000', False),
)

ISSUE_STATUSES = (
    (1, _("New"), False, '#8C2318', True),
    (2, _("In progress"), False, '#5E8C6A', False),
    (3, _("Ready for test"), True, '#88A65E', False),
    (4, _("Closed"), True, '#BFB35A', False),
    (5, _("Needs Info"), False, '#89BAB4', False),
    (6, _("Rejected"), True, '#CC0000', False),
    (7, _("Postponed"), False, '#666666', False),
)

ISSUE_TYPES = (
    (1, _(u'Bug'), '#89BAB4', True),
)

QUESTION_STATUS = (
    (1, _("Pending"), False, 'orange', True),
    (2, _("Answered"), False, '#669933', False),
    (3, _("Closed"), True,'#BFB35A', False),
)

