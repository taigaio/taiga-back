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

import uuid


# Centralized uuid attachment and ref generation
@receiver(signals.pre_save)
def attach_uuid(sender, instance, **kwargs):
    fields = sender._meta.init_name_map()
    #fields = sender._meta.get_all_field_names()

    if "modified_date" in fields:
        instance.modified_date = now()

    # if sender class does not have uuid field.
    if "uuid" in fields:
        if not instance.uuid:
            instance.uuid = unicode(uuid.uuid1())


# Centraliced reference assignation.
@receiver(signals.pre_save, sender=Task)
@receiver(signals.pre_save, sender=UserStory)
def attach_unique_reference(sender, instance, **kwargs):
    project = Project.objects.select_for_update().filter(pk=instance.project_id).get()
    if isinstance(instance, Task):
        project.last_task_ref += 1
        instance.ref = project.last_task_ref
    else:
        project.last_us_ref += 1
        instance.ref = project.last_us_ref

    project.save()


class User(AbstractUser):
    color = models.CharField(max_length=9)
    description = models.TextField(blank=True)
    photo = models.FileField(upload_to="files/msg", max_length=500, null=True, blank=True)
    default_language = models.CharField(max_length=20, null=True, blank=True, default=None)
    default_timezone = models.CharField(max_length=20, null=True, blank=True, default=None)
    token = models.CharField(max_length=200, unique=True, null=True, blank=True, default=None)
    colorize_tags = models.BooleanField(default=False)
    objects = UserManager()


class Role(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    permissions = models.ManyToManyField('auth.Permission',
        verbose_name=_('permissions'), blank=True)

    def __unicode__(self):
        return unicode(self.name)
