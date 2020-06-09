# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0003_auto_20150410_0829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeline',
            name='project',
            field=models.ForeignKey(null=True, to='projects.Project', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
