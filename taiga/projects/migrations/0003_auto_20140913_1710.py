# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0002_auto_20140903_0920'),
    ]

    operations = [
        migrations.RenameField(
            model_name='membership',
            old_name='invited_by_id',
            new_name='invited_by_id_old',
        ),

        migrations.AddField(
            model_name='membership',
            name='invited_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, related_name='ihaveinvited+'),
            preserve_default=True,
        ),

        migrations.RunSQL("UPDATE projects_membership SET invited_by_id = invited_by_id_old"),

        migrations.RemoveField(
            model_name='membership',
            name='invited_by_id_old',
        ),

    ]
