# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0017_fix_is_private_for_projects'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='issues_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='tasks_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='userstories_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
    ]
