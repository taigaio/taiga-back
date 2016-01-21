# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0035_project_blocked_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='transfer_token',
            field=models.CharField(max_length=255, default=None, blank=True, null=True, verbose_name='project transfer token'),
        ),
    ]
