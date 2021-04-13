# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Like(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        related_name="likes",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
    )
    created_date = models.DateTimeField(null=False, blank=False, auto_now_add=True,
                                        verbose_name=_("created date"))

    class Meta:
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")
        unique_together = ("content_type", "object_id", "user")

    @property
    def project(self):
        if hasattr(self.content_object, 'project'):
            return self.content_object.project
        return None

    def __str__(self):
        return self.user.get_full_name()
