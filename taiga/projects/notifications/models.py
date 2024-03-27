# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from taiga.base.db.models.fields import JSONField
from taiga.projects.history.choices import HISTORY_TYPE_CHOICES

from .choices import NOTIFY_LEVEL_CHOICES, NotifyLevel


class NotifyPolicy(models.Model):
    """
    This class represents a persistence for
    project user notifications preference.
    """
    project = models.ForeignKey("projects.Project", related_name="notify_policies", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notify_policies", on_delete=models.CASCADE)
    notify_level = models.SmallIntegerField(choices=NOTIFY_LEVEL_CHOICES)
    live_notify_level = models.SmallIntegerField(choices=NOTIFY_LEVEL_CHOICES, default=NotifyLevel.involved)
    web_notify_level = models.BooleanField(default=True, null=False, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField()
    _importing = None

    class Meta:
        unique_together = ("project", "user",)
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self._importing or not self.modified_date:
            self.modified_at = timezone.now()

        return super().save(*args, **kwargs)


class HistoryChangeNotification(models.Model):
    """
    This class controls the pending notifications for an object, it should be instantiated
    or updated when an object requires notifications.
    """
    key = models.CharField(max_length=255, unique=False, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        verbose_name=_("owner"),
        related_name="+",
        on_delete=models.CASCADE,
    )
    created_datetime = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                            verbose_name=_("created date time"))
    updated_datetime = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                            verbose_name=_("updated date time"))
    history_entries = models.ManyToManyField("history.HistoryEntry",
                                             verbose_name=_("history entries"),
                                             related_name="+")
    notify_users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                             verbose_name=_("notify users"),
                                             related_name="+")
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        verbose_name=_("project"),
        related_name="+",
        on_delete=models.CASCADE,
    )

    history_type = models.SmallIntegerField(choices=HISTORY_TYPE_CHOICES)

    class Meta:
        unique_together = ("key", "owner", "project", "history_type")


class Watched(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        related_name="watched",
        verbose_name=_("user"),
        on_delete=models.CASCADE
    )
    created_date = models.DateTimeField(auto_now_add=True, null=False, blank=False,
                                        verbose_name=_("created date"))
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        verbose_name=_("project"),
        related_name="watched",
        on_delete=models.CASCADE
    )
    class Meta:
        verbose_name = _("Watched")
        verbose_name_plural = _("Watched")
        unique_together = ("content_type", "object_id", "user", "project")


class WebNotification(models.Model):
    created = models.DateTimeField(default=timezone.now, db_index=True)
    read = models.DateTimeField(default=None, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="web_notifications",
        on_delete=models.CASCADE
    )
    event_type = models.PositiveIntegerField()
    data = JSONField()
