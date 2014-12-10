# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.template.defaultfilters import slugify


def fix_project_template_slugs(apps, schema_editor):
    ProjectTemplate = apps.get_model("projects", "ProjectTemplate")
    for pt in ProjectTemplate.objects.all():
        for us_status in pt.us_statuses:
            us_status["slug"] = slugify(us_status["name"])
        for task_status in pt.task_statuses:
            task_status["slug"] = slugify(task_status["name"])
        for issue_status in pt.issue_statuses:
            issue_status["slug"] = slugify(issue_status["name"])
        pt.save()

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20141028_2057'),
    ]

    operations = [
            migrations.RunPython(fix_project_template_slugs),
    ]
