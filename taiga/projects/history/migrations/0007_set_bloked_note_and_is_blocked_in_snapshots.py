# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
from django.core.exceptions import ObjectDoesNotExist
from taiga.projects.history.services import (make_key_from_model_object,
    get_model_from_key,
    get_pk_from_key)


def set_current_values_of_blocked_note_and_is_blocked_to_the_last_snapshot(apps, schema_editor):
    HistoryEntry = apps.get_model("history", "HistoryEntry")

    for history_entry in HistoryEntry.objects.filter(is_snapshot=True).order_by("created_at"):
        model = get_model_from_key(history_entry.key)
        pk = get_pk_from_key(history_entry.key)
        try:
            obj = model.objects.get(pk=pk)
            save = False
            if hasattr(obj, "is_blocked") and "is_blocked" not in history_entry.snapshot:
                history_entry.snapshot["is_blocked"] = obj.is_blocked
                save = True

            if hasattr(obj, "blocked_note") and "blocked_note" not in history_entry.snapshot:
                history_entry.snapshot["blocked_note"] = obj.blocked_note
                save = True

            if save:
                history_entry.save()

        except ObjectDoesNotExist as e:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0006_fix_json_field_not_null'),
        ('userstories', '0009_remove_userstory_is_archived'),
        ('tasks', '0005_auto_20150114_0954'),
        ('issues', '0004_auto_20150114_0954'),
    ]

    operations = [
        migrations.RunPython(set_current_values_of_blocked_note_and_is_blocked_to_the_last_snapshot),
    ]
