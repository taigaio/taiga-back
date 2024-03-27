# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_auto_20150623_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='milestone',
            field=models.ForeignKey(to='milestones.Milestone', related_name='tasks', default=None, verbose_name='milestone', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True),
            preserve_default=True,
        ),
    ]
