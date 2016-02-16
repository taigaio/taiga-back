# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taiga.projects.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0030_auto_20151128_0757'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='logo',
            field=models.FileField(null=True, blank=True, upload_to=taiga.projects.models.get_project_logo_file_path, verbose_name='logo', max_length=500),
        ),
    ]
