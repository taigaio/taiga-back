# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_pgjson.fields

def change_fk_with_tuple_pk_and_name(apps, schema_editor):
    HistoryEntry = apps.get_model("history", "HistoryEntry")

    for item in HistoryEntry.objects.all():
        if item.delete_comment_user_old:
            item.delete_comment_user = {"pk": item.delete_comment_user_old.pk, "name": item.delete_comment_user_old.name}
        else:
            item.delete_comment_user = None
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('history', '0002_auto_20140916_0936'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historyentry',
            old_name='delete_comment_user',
            new_name='delete_comment_user_old',
        ),
        migrations.AddField(
            model_name='historyentry',
            name='delete_comment_user',
            field=django_pgjson.fields.JsonField(null=True, blank=True, default=None),
            preserve_default=True,
        ),

        migrations.RunPython(change_fk_with_tuple_pk_and_name),

        migrations.RemoveField(
            model_name='historyentry',
            name='delete_comment_user_old',
        ),
    ]
