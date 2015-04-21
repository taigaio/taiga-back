# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0019_auto_20150311_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='user_order',
            field=models.IntegerField(default=10000, verbose_name='user order'),
            preserve_default=True,
        ),
    ]
