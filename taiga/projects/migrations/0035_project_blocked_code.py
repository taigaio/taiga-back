# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0034_project_looking_for_people_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='blocked_code',
            field=models.CharField(choices=[('blocked-by-staff', 'This project was blocked by staff'), ('blocked-by-owner-leaving', 'This project was because the owner left')], null=True, default=None, max_length=255, blank=True, verbose_name='blocked code'),
        ),
    ]
