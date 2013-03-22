# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission, Group


class Profile(models.Model):
    user = models.OneToOneField("auth.User", related_name='profile')
    description = models.TextField(blank=True)
    photo = models.FileField(upload_to="files/msg", max_length=500, null=True,
                             blank=True)

    default_language = models.CharField(max_length=20, null=True, blank=True,
                                        default=None)
    default_timezone = models.CharField(max_length=20, null=True, blank=True,
                                        default=None)
    token = models.CharField(max_length=200, unique=True, null=True,
                             blank=True, default=None)
    colorize_tags = models.BooleanField(default=False)


class Role(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    permissions = models.ManyToManyField(Permission,
        verbose_name=_('permissions'), blank=True)

    def __unicode__(self):
        return unicode(self.name)

if not hasattr(Group, 'role'):
    field = models.ForeignKey(Role, blank=False, null=False, related_name='groups')
    field.contribute_to_class(Group, 'role')


from . import sigdispatch
