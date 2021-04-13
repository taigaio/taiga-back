# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContactEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contact_entries",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )

    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="contact_entries",
        verbose_name=_("project"),
        on_delete=models.CASCADE,
    )

    comment = models.TextField(null=False, blank=False, verbose_name=_("comment"))

    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = "contact entry"
        verbose_name_plural = "contact entries"
        ordering = ["-created_date", "id"]
