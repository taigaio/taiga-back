# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _


class FeedbackEntry(models.Model):
    full_name = models.CharField(null=False, blank=False, max_length=256,
                                 verbose_name=_('full name'))
    email = models.EmailField(null=False, blank=False, max_length=255,
                              verbose_name=_('email address'))
    comment = models.TextField(null=False, blank=False,
                               verbose_name=_("comment"))
    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = "feedback entry"
        verbose_name_plural = "feedback entries"
        ordering = ["-created_date", "id"]
