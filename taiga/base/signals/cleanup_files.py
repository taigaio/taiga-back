# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import apps
from django.db import models, connection
from django.db.models.signals import pre_save, post_delete
from django.dispatch import Signal

import logging

logger = logging.getLogger(__name__)


cleanup_pre_delete = Signal()
cleanup_post_delete = Signal()


def _find_models_with_filefield():
    result = []
    for model in apps.get_models():
        for field in model._meta.fields:
            if isinstance(field, models.FileField):
                result.append(model)
                break
    return result


def _delete_file(file_obj):
    def delete_from_storage():
        try:
            cleanup_pre_delete.send(sender=None, file=file_obj)
            storage.delete(file_obj.name)
            cleanup_post_delete.send(sender=None, file=file_obj)
        except Exception:
            logger.exception("Unexpected exception while attempting "
                             "to delete old file '%s'".format(file_obj.name))

    storage = file_obj.storage
    if storage and storage.exists(file_obj.name):
        connection.on_commit(delete_from_storage)


def _get_file_fields(instance):
    return filter(
        lambda field: isinstance(field, models.FileField),
        instance._meta.fields,
    )


def remove_files_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except instance.DoesNotExist:
        return

    for field in _get_file_fields(instance):
        old_file = getattr(old_instance, field.name)
        new_file = getattr(instance, field.name)

        if old_file and old_file != new_file:
            _delete_file(old_file)


def remove_files_on_delete(sender, instance, **kwargs):
    for field in _get_file_fields(instance):
        file_to_delete = getattr(instance, field.name)

        if file_to_delete:
            _delete_file(file_to_delete)


def connect_cleanup_files_signals():
    for model in _find_models_with_filefield():
        pre_save.connect(remove_files_on_change, sender=model)
        post_delete.connect(remove_files_on_delete, sender=model)
