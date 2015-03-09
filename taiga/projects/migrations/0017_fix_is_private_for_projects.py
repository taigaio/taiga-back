# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def update_existing_projects(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(is_private=False).update(is_private=True)

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0016_fix_json_field_not_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='is_private',
            field=models.BooleanField(verbose_name='is private', default=True),
            preserve_default=True,
        ),
        migrations.RunPython(update_existing_projects),
    ]
