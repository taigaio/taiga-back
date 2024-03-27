# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class InstanceTelemetry(models.Model):
    instance_id = models.CharField(
        null=False,
        blank=False,
        max_length=100,
        verbose_name=_("instance id")
    )
    created_at = models.DateTimeField(default=timezone.now,
            verbose_name=_("created at"))

    class Meta:
        verbose_name = "instance telemetry"
        verbose_name_plural = "instances telemetries"

    def __str__(self):
        return self.instance_id
