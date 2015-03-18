# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.exceptions import ObjectDoesNotExist
from taiga.projects.history.services import (make_key_from_model_object,
    get_model_from_key,
    get_pk_from_key)


def update_many(objects, fields=[], using="default"):
    """Update list of Django objects in one SQL query, optionally only
    overwrite the given fields (as names, e.g. fields=["foo"]).
    Objects must be of the same Django model. Note that save is not
    called and signals on the model are not raised."""
    if not objects:
        return

    import django.db.models
    from django.db import connections
    con = connections[using]

    names = fields
    meta = objects[0]._meta
    fields = [f for f in meta.fields if not isinstance(f, django.db.models.AutoField) and (not names or f.name in names)]

    if not fields:
        raise ValueError("No fields to update, field names are %s." % names)

    fields_with_pk = fields + [meta.pk]
    parameters = []
    for o in objects:
        parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields_with_pk))

    table = meta.db_table
    assignments = ",".join(("%s=%%s"% con.ops.quote_name(f.column)) for f in fields)
    con.cursor().executemany(
        "update %s set %s where %s=%%s" % (table, assignments, con.ops.quote_name(meta.pk.column)),
        parameters)


def set_current_values_of_blocked_note_and_is_blocked_to_the_last_snapshot(apps, schema_editor):
    HistoryEntry = apps.get_model("history", "HistoryEntry")
    updatingEntries = []

    for history_entry in HistoryEntry.objects.filter(is_snapshot=True).order_by("created_at"):
        model = get_model_from_key(history_entry.key)
        pk = get_pk_from_key(history_entry.key)
        try:
            print("Fixing history_entry: ", history_entry.created_at)
            obj = model.objects.get(pk=pk)
            save = False
            if hasattr(obj, "is_blocked") and "is_blocked" not in history_entry.snapshot:
                history_entry.snapshot["is_blocked"] = obj.is_blocked
                save = True

            if hasattr(obj, "blocked_note") and "blocked_note" not in history_entry.snapshot:
                history_entry.snapshot["blocked_note"] = obj.blocked_note
                save = True

            if save:
                updatingEntries.append(history_entry)

        except ObjectDoesNotExist as e:
            print("Ignoring {}".format(history_entry.pk))

    update_many(updatingEntries)

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
