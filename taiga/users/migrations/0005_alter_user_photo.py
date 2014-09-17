# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taiga.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20140913_1914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.FileField(upload_to=taiga.users.models.get_user_file_path, blank=True, max_length=500, verbose_name='photo', null=True),
        ),
    ]
