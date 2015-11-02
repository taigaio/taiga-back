# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0026_auto_20150911_1237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='total_milestones',
            field=models.IntegerField(verbose_name='total of milestones', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='project',
            name='total_story_points',
            field=models.FloatField(verbose_name='total story points', null=True, blank=True),
            preserve_default=True,
        ),
    ]
