from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic


class Votes(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType")
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey("content_type", "object_id")
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Votes")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id")

    def __str__(self):
        return self.count


class Vote(models.Model):
    content_type = models.ForeignKey("contenttypes.ContentType")
    object_id = models.PositiveIntegerField(null=False)
    content_object = generic.GenericForeignKey("content_type", "object_id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, blank=False,
                             related_name="votes", verbose_name=_("votes"))

    class Meta:
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
        unique_together = ("content_type", "object_id", "user")

    def __str__(self):
        return self.user
