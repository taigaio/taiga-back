# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_auto_20141002_2337'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='invitation_extra_text',
            field=models.TextField(null=True, verbose_name='invitation extra text', blank=True),
            preserve_default=True,
        ),
    ]
