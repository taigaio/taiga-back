# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0010_remove_userstory_watchers'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstory',
            name='tribe_gig',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, default=None, verbose_name='taiga tribe gig', blank=True),
        ),
    ]
