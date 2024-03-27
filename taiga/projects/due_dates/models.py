# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.utils.translation import gettext_lazy as _


class DueDateMixin(models.Model):
    due_date = models.DateField(
        blank=True, null=True, default=None, verbose_name=_('due date'),
    )
    due_date_reason = models.TextField(
        null=False, blank=True, default='', verbose_name=_('reason for the due date'),
    )

    class Meta:
        abstract = True
