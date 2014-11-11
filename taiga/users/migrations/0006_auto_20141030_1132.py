# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_system',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='github_id',
            field=models.IntegerField(blank=True, null=True, db_index=True, verbose_name='github ID'),
        ),
    ]
