# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver


class BlockedMixin(models.Model):
    is_blocked = models.BooleanField(default=False, null=False, blank=True,
                                     verbose_name=_("is blocked"))
    blocked_note = models.TextField(default="", null=False, blank=True,
                                   verbose_name=_("blocked note"))
    class Meta:
        abstract = True


@receiver(models.signals.pre_save, dispatch_uid='blocked_pre_save')
def blocked_pre_save(sender, instance, **kwargs):
    if  isinstance(instance, BlockedMixin) and not instance.is_blocked:
        instance.blocked_note = ""
