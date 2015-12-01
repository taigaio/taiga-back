# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('likes', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='likes',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='likes',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Likes',
        ),
    ]
