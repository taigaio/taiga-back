# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.utils.translation import gettext_lazy as _

from taiga.base.db.models.fields import JSONField


class Webhook(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        null=False,
        blank=False,
        related_name="webhooks",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=250, null=False, blank=False,
                            verbose_name=_("name"))
    url = models.URLField(null=False, blank=False, verbose_name=_("URL"))
    key = models.TextField(null=False, blank=False, verbose_name=_("secret key"))

    class Meta:
        ordering = ['name', '-id']


class WebhookLog(models.Model):
    webhook = models.ForeignKey(
        Webhook,
        null=False,
        blank=False,
        related_name="logs",
        on_delete=models.CASCADE,
    )
    url = models.URLField(null=False, blank=False, verbose_name=_("URL"))
    status = models.IntegerField(null=False, blank=False, verbose_name=_("status code"))
    request_data = JSONField(null=False, blank=False, verbose_name=_("request data"))
    request_headers = JSONField(null=False, blank=False, verbose_name=_("request headers"), default=dict)
    response_data = models.TextField(null=False, blank=False, verbose_name=_("response data"))
    response_headers = JSONField(null=False, blank=False, verbose_name=_("response headers"), default=dict)
    duration = models.FloatField(null=False, blank=False, verbose_name=_("duration"), default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created', '-id']
