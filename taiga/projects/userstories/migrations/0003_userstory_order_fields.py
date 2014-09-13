# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models import F

def copy_backlog_order_to_kanban_order(apps, schema_editor):
    UserStory = apps.get_model("userstories", "UserStory")
    UserStory.objects.all().update(kanban_order=F("backlog_order"))


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0002_auto_20140903_1301'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userstory',
            options={'verbose_name_plural': 'user stories', 'ordering': ['project', 'backlog_order', 'ref'], 'verbose_name': 'user story', 'permissions': (('view_userstory', 'Can view user story'),)},
        ),
        migrations.RenameField(
            model_name='userstory',
            old_name='order',
            new_name='backlog_order',
        ),

        migrations.AlterField(
            model_name='userstory',
            name='backlog_order',
            field=models.IntegerField(default=1, verbose_name='backlog order'),
        ),

        migrations.AddField(
            model_name='userstory',
            name='sprint_order',
            field=models.IntegerField(default=1, verbose_name='sprint order'),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='userstory',
            name='kanban_order',
            field=models.IntegerField(default=1, verbose_name='sprint order'),
            preserve_default=True,
        ),

        migrations.RunPython(copy_backlog_order_to_kanban_order),
    ]
