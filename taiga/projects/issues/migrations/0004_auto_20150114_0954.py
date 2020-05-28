# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0003_auto_20141210_1108'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='issue',
            options={'ordering': ['project', '-id'], 'verbose_name_plural': 'issues', 'verbose_name': 'issue'},
        ),
    ]
