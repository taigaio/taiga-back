# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0036_project_transfer_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='blocked_code',
            field=models.CharField(max_length=255, blank=True, verbose_name='blocked code', choices=[('blocked-by-staff', 'This project was blocked by staff'), ('blocked-by-owner-leaving', 'This project was blocked because the owner left')], null=True, default=None),
        ),
    ]
