# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import connection
from django.conf import settings
from django.utils import timezone

from taiga.projects.history import services as history_service
from taiga.projects.history.choices import HistoryType

from . import tasks


def _get_project_webhooks(project):
    webhooks = []
    for webhook in project.webhooks.all():
        webhooks.append({
            "id": webhook.pk,
            "url": webhook.url,
            "key": webhook.key,
        })
    return webhooks


def on_new_history_entry(sender, instance, created, **kwargs):
    if not settings.WEBHOOKS_ENABLED:
        return None

    if instance.is_hidden:
        return None

    model = history_service.get_model_from_key(instance.key)
    pk = history_service.get_pk_from_key(instance.key)
    try:
        obj = model.objects.get(pk=pk)
    except model.DoesNotExist:
        # Catch simultaneous DELETE request
        return None

    webhooks = _get_project_webhooks(obj.project)

    if instance.type == HistoryType.create:
        task = tasks.create_webhook
        extra_args = []
    elif instance.type == HistoryType.change:
        task = tasks.change_webhook
        extra_args = [instance]
    elif instance.type == HistoryType.delete:
        task = tasks.delete_webhook
        extra_args = []

    by = instance.owner
    date = timezone.now()

    webhooks_args = []
    for webhook in webhooks:
        args = [webhook["id"], webhook["url"], webhook["key"], by, date, obj] + extra_args
        webhooks_args.append(args)

    connection.on_commit(lambda: _execute_task(task, webhooks_args))


def _execute_task(task, webhooks_args):
    for webhook_args in webhooks_args:

        if settings.CELERY_ENABLED:
            task.delay(*webhook_args)
        else:
            task(*webhook_args)
