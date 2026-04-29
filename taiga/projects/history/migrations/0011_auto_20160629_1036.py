# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

BATCH_SIZE = 1000  # safe batch size for large tables

def populate_project(apps, schema_editor):
    HistoryEntry = apps.get_model('history', 'HistoryEntry')
    # Import the Taiga helper function
    from taiga.projects.history.services import get_instance_from_key

    total = HistoryEntry.objects.count()
    for start in range(0, total, BATCH_SIZE):
        batch = HistoryEntry.objects.all()[start:start + BATCH_SIZE]
        entries_to_update = []
        for entry in batch:
            instance = get_instance_from_key(entry.key)
            if instance and hasattr(instance, 'project'):
                entry.project = instance.project
                entries_to_update.append(entry)
        if entries_to_update:
            HistoryEntry.objects.bulk_update(entries_to_update, ['project'])


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0010_historyentry_project'),
        ('wiki', '0003_auto_20160615_0721'),
        ('users', '0022_auto_20160629_1443'),
    ]

    operations = [
        # Populate the existing project ForeignKey field
        migrations.RunPython(
            code=populate_project,
            reverse_code=migrations.RunPython.noop
        ),
    ]