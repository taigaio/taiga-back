# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhook',
            name='name',
            field=models.CharField(max_length=250, default='webhook', verbose_name='name'),
            preserve_default=False,
        ),
    ]
