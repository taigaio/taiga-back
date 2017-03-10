# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.apps import apps
from django.db import models, connection
from django.db.models.signals import pre_save, post_delete
from django.dispatch import Signal

import logging

logger = logging.getLogger(__name__)


cleanup_pre_delete = Signal(providing_args=["file"])
cleanup_post_delete = Signal(providing_args=["file"])


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
