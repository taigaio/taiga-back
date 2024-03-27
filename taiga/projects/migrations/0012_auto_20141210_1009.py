# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
