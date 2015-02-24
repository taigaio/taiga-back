# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0003_auto_20150122_1021'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='webhook',
            options={'ordering': ['name', '-id']},
        ),
        migrations.AlterModelOptions(
            name='webhooklog',
            options={'ordering': ['-created', '-id']},
        ),
    ]
