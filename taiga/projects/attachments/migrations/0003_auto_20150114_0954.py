# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_add_size_and_name_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachment',
            options={'ordering': ['project', 'created_date', 'id'], 'verbose_name_plural': 'attachments', 'verbose_name': 'attachment'},
        ),
    ]
