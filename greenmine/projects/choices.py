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
    (1, _(u'Low'), False),
    (3, _(u'Normal'), True),
    (5, _(u'High'), False),
)

SEVERITY_CHOICES = (
    (1, _(u'Wishlist'), False),
    (2, _(u'Minor'), False),
    (3, _(u'Normal'), True),
    (4, _(u'Important'), False),
    (5, _(u'Critical'), False),
)

ISSUE_STATUSES = (
    (1, _("New"), False, True),
    (2, _("In progress"), False, False),
    (3, _("Ready for test"), True, False),
    (4, _("Closed"), True, False),
    (5, _("Needs Info"), False, False),
    (6, _("Rejected"), True, False),
    (7, _("Postponed"), False, False),
)

ISSUE_TYPES = (
    (1, _(u'Bug'), True),
)

QUESTION_STATUS = (
    (1, _("Pending"), False, True),
    (2, _("Answered"), False, False),
    (3, _("Closed"), True, False),
)

# TODO: pending to refactor

TASK_COMMENT = 1
TASK_STATUS_CHANGE = 2
TASK_PRIORITY_CHANGE = 3
TASK_ASSIGNATION_CHANGE = 4

TASK_CHANGE_CHOICES = (
    (TASK_COMMENT, _("Task comment")),
    (TASK_STATUS_CHANGE, _("Task status change")),
    (TASK_PRIORITY_CHANGE, _("Task prioriy change")),
    (TASK_ASSIGNATION_CHANGE, _("Task assignation change")),
)
