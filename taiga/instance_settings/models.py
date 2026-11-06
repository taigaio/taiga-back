# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf import settings
from django.db import models
from django.utils import timezone


class InstanceDefaults(models.Model):
    """One row of nullable admin overrides. Environment defaults stay external."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    default_language = models.CharField(max_length=20, blank=True, default="")
    default_theme = models.CharField(max_length=100, blank=True, default="")
    revision = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.pk != 1:
            raise ValueError("Only one instance defaults row is allowed")
        return super().save(*args, **kwargs)


class InstanceDefaultsAudit(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(default=timezone.now)
    old_language = models.CharField(max_length=20, blank=True)
    new_language = models.CharField(max_length=20, blank=True)
    old_theme = models.CharField(max_length=100, blank=True)
    new_theme = models.CharField(max_length=100, blank=True)
    revision = models.PositiveIntegerField()
