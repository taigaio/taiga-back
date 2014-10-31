# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def update_total_milestones(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    qs = Project.objects.filter(total_milestones__isnull=True)
    qs.update(total_milestones=0)


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0005_membership_invitation_extra_text'),
    ]

    operations = [
        migrations.RunPython(update_total_milestones),
        migrations.AlterField(
            model_name='project',
            name='total_milestones',
            field=models.IntegerField(null=False, blank=False, default=0, verbose_name='total of milestones'),
        ),
    ]
