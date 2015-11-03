# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20151005_1357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifypolicy',
            name='notify_level',
            field=models.SmallIntegerField(choices=[(1, 'Involved'), (2, 'All'), (3, 'None')]),
        ),
    ]
