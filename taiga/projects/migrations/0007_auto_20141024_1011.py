# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_auto_20141029_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuestatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taskstatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userstorystatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255, null=True),
            preserve_default=True,
        ),
    ]
