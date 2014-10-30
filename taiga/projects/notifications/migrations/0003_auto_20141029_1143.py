# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_historychangenotification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='historychangenotification',
            unique_together=set([('key', 'owner', 'project', 'history_type')]),
        ),
    ]
