# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _


US_STATUSES = (
    (1, _(u"Open"), False),
    (2, _(u"Closed"), True),
)

TASK_STATUSES = (
    (1, _(u"New"), False, "#999999"),
    (2, _(u"In progress"), False, "#ff9900"),
    (3, _(u"Ready for test"), True, "#ffcc00"),
    (4, _(u"Closed"), True, "#669900"),
    (5, _(u"Needs Info"), False, "#999999"),
)

POINTS_CHOICES = (
    (1, u'?', None),
    (2,  u'0', 0),
    (3, u'1/2', 0.5),
    (4,  u'1', 1),
    (5,  u'2', 2),
    (6,  u'3', 3),
    (7,  u'5', 5),
    (8,  u'8', 8),
    (9, u'10', 10),
    (10, u'15', 15),
    (11, u'20', 20),
    (12, u'40', 40),
)

PRIORITY_CHOICES = (
    (1, _(u'Low')),
    (3, _(u'Normal')),
    (5, _(u'High')),
)

SEVERITY_CHOICES = (
    (1, _(u'Wishlist')),
    (2, _(u'Minor')),
    (3, _(u'Normal')),
    (4, _(u'Important')),
    (5, _(u'Critical')),
)

ISSUE_STATUSES = (
    (1, _(u"New"), False),
    (2, _(u"In progress"), False),
    (3, _(u"Ready for test"), True),
    (4, _(u"Closed"), True),
    (5, _(u"Needs Info"), False),
    (6, _(u"Rejected"), True),
    (7, _(u"Postponed"), False),
)

ISSUE_TYPES = (
    (1, _(u'Bug')),
)

QUESTION_STATUS = (
    (1, _(u"New"), False),
    (2, _(u"Pending"), False),
    (3, _(u"Answered"), True),
)

# TODO: pending to refactor

TASK_COMMENT = 1
TASK_STATUS_CHANGE = 2
TASK_PRIORITY_CHANGE = 3
TASK_ASSIGNATION_CHANGE = 4

TASK_CHANGE_CHOICES = (
    (TASK_COMMENT, _(u"Task comment")),
    (TASK_STATUS_CHANGE, _(u"Task status change")),
    (TASK_PRIORITY_CHANGE, _(u"Task prioriy change")),
    (TASK_ASSIGNATION_CHANGE, _(u"Task assignation change")),
)
