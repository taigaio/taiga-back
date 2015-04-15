# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20150213_1701'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='default_language',
            new_name='lang',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='default_timezone',
            new_name='timezone',
        ),
    ]
