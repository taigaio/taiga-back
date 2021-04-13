# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
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
