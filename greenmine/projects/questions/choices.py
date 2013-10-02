# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

QUESTION_STATUS = (
    (1, _(u"New"), False),
    (2, _(u"Pending"), False),
    (3, _(u"Answered"), True),
)
