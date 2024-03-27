# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0026_auto_20150911_1237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='total_milestones',
            field=models.IntegerField(verbose_name='total of milestones', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='project',
            name='total_story_points',
            field=models.FloatField(verbose_name='total story points', null=True, blank=True),
            preserve_default=True,
        ),
    ]
