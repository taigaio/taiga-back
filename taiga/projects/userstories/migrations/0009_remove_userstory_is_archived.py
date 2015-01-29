# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0008_auto_20141210_1107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userstory',
            name='is_archived',
        ),
    ]
