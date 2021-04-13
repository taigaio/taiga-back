# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


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
