# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20150326_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='lang',
            field=models.CharField(max_length=20, blank=True, null=True, default='', verbose_name='default language'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(max_length=20, blank=True, null=True, default='', verbose_name='default timezone'),
            preserve_default=True,
        ),
    ]
