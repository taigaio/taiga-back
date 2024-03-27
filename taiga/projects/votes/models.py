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


class Votes(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    count = models.PositiveIntegerField(null=False, blank=False, default=0, verbose_name=_("count"))

    class Meta:
        verbose_name = _("Votes")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id")

    @property
    def project(self):
        if hasattr(self.content_object, 'project'):
            return self.content_object.project
        return None

    def __str__(self):
        return self.count


class Vote(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        related_name="votes",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id", "user")

    @property
    def project(self):
        if hasattr(self.content_object, 'project'):
            return self.content_object.project
        return None

    def __str__(self):
        return self.user.get_full_name()
