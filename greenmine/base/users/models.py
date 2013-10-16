# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import UserManager, AbstractUser

from greenmine.base.notifications.models import WatcherMixin


class User(WatcherMixin, AbstractUser):
    color = models.CharField(max_length=9, null=False, blank=True, default="#669933",
                             verbose_name=_('color'))
    description = models.TextField(null=False, blank=True,
                                   verbose_name=_('description'))
    photo = models.FileField(upload_to='files/msg', max_length=500, null=True, blank=True,
                             verbose_name=_('photo'))
    default_language = models.CharField(max_length=20, null=False, blank=True, default='',
                                        verbose_name=_('default language'))
    default_timezone = models.CharField(max_length=20, null=False, blank=True, default='',
                                        verbose_name=_('default timezone'))
    token = models.CharField(max_length=200, null=True, blank=True, default=None,
                             verbose_name=_('token'))
    colorize_tags = models.BooleanField(null=False, blank=True, default=False,
                                        verbose_name=_('colorize tags'))
    objects = UserManager()

    class Meta:
        ordering = ["username"]


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

    def __str__(self):
        return self.name
