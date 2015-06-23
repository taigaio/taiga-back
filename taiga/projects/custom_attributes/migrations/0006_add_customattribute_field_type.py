# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0005_auto_20150505_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuecustomattribute',
            name='field_type',
            field=models.CharField(default='TEXT', max_length=5, verbose_name='attribute field type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taskcustomattribute',
            name='field_type',
            field=models.CharField(default='TEXT', max_length=5, verbose_name='attribute field type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userstorycustomattribute',
            name='field_type',
            field=models.CharField(default='TEXT', max_length=5, verbose_name='attribute field type'),
            preserve_default=True,
        ),

    ]
