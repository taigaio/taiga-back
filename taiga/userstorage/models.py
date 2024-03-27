# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from taiga.base.db.models.fields import JSONField


class StorageEntry(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        related_name="storage_entries",
        verbose_name=_("owner"),
        on_delete=models.CASCADE,
    )
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    modified_date = models.DateTimeField(auto_now=True, null=False, blank=False,
                                         verbose_name=_("modified date"))
    key = models.CharField(max_length=255, null=False, blank=False, verbose_name=_("key"))
    value = JSONField(blank=True, default=None, null=True, verbose_name=_("value"))

    class Meta:
        verbose_name = "storage entry"
        verbose_name_plural = "storages entries"
        unique_together = ("owner", "key")
        ordering = ["owner", "key"]
