# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0004_auto_20150508_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='sha1',
            field=models.CharField(default='', verbose_name='sha1', max_length=40, blank=True),
            preserve_default=True,
        ),
    ]