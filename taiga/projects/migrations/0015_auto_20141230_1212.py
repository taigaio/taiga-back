# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations


def fix_project_template_us_status_archived(apps, schema_editor):
    ProjectTemplate = apps.get_model("projects", "ProjectTemplate")
    for pt in ProjectTemplate.objects.all():
        for us_status in pt.us_statuses:
            us_status["is_archived"] = False

        pt.us_statuses.append({
            "color": "#5c3566",
            "order": 6,
            "is_closed": True,
            "is_archived": True,
            "wip_limit": None,
            "name": "Archived",
            "slug": "archived"})

        pt.save()

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_userstorystatus_is_archived'),
    ]

    operations = [
        migrations.RunPython(fix_project_template_us_status_archived),
    ]
