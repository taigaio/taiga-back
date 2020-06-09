# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolepoints',
            name='points',
            field=models.ForeignKey(related_name='role_points', to='projects.Points', null=True, verbose_name='points', on_delete=models.CASCADE),
        ),
    ]
