# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

##########
# MODELS #
##########

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver


class BlockedMixin(models.Model):
    is_blocked = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is blocked"))
    blocked_note = models.TextField(default="", null=False, blank=True,
                                   verbose_name=_("blocked note"))
    class Meta:
        abstract = True


@receiver(models.signals.pre_save, dispatch_uid='blocked_pre_save')
def blocked_pre_save(sender, instance, **kwargs):
    if  isinstance(instance, BlockedMixin) and not instance.is_blocked:
        instance.blocked_note = ""
