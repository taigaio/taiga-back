# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
