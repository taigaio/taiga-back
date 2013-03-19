# -*- coding: utf-8 -*-

from django.db.models import signals
from django.dispatch import receiver
from django.db import models
from django.utils.timezone import now

from ..scrum.models import Project, UserStory, Task

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
