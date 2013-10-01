# -*- coding: utf-8 -*-

from django.db.models import signals
from django.utils.timezone import now
from django.dispatch import receiver

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


# Patch api view for correctly return 401 responses on
# request is authenticated instead of 403
from .monkey import patch_api_view; patch_api_view()
