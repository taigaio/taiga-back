# -*- coding: utf-8 -*-

import uuid

from django.db.models import signals
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.utils.timezone import now
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import UserManager, AbstractUser, Group

from greenmine.scrum.models import Project, UserStory, Task
from greenmine.base.notifications.models import WatcherMixin

import uuid


# Centralized uuid attachment and ref generation
@receiver(signals.pre_save)
def attach_uuid(sender, instance, **kwargs):
    fields = sender._meta.init_name_map()

    if 'modified_date' in fields:
        instance.modified_date = now()

    # if sender class does not have uuid field.
    if 'uuid' in fields:
        if not instance.uuid:
            instance.uuid = unicode(uuid.uuid1())


class User(WatcherMixin, AbstractUser):
    color = models.CharField(max_length=9, null=False, blank=False, default="#669933",
                             verbose_name=_('color'))
    description = models.TextField(null=False, blank=True,
                                   verbose_name=_('description'))
    photo = models.FileField(upload_to='files/msg', max_length=500, null=True, blank=True,
                             verbose_name=_('photo'))
    default_language = models.CharField(max_length=20, null=False, blank=True, default='',
                                        verbose_name=_('default language'))
    default_timezone = models.CharField(max_length=20, null=False, blank=True, default='',
                                        verbose_name=_('default timezone'))
    token = models.CharField(max_length=200, null=False, blank=True, default='',
                             verbose_name=_('token'))
    colorize_tags = models.BooleanField(null=False, blank=True, default=False,
                                        verbose_name=_('colorize tags'))
    objects = UserManager()


class Role(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False,
                verbose_name=_('name'))
    slug = models.SlugField(max_length=250, unique=True, null=False, blank=True,
                verbose_name=_('slug'))
    permissions = models.ManyToManyField('auth.Permission',
                related_name='roles',
                verbose_name=_('permissions'))

    class Meta:
        verbose_name = u'role'
        verbose_name_plural = u'roles'
        ordering = ['slug']

    def __unicode__(self):
        return self.name


# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from .monkey import patch_api_view; patch_api_view()
