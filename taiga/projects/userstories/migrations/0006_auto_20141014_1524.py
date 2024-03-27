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
        ('userstories', '0005_auto_20141009_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstory',
            name='backlog_order',
            field=models.IntegerField(default=10000, verbose_name='backlog order'),
        ),
        migrations.AlterField(
            model_name='userstory',
            name='kanban_order',
            field=models.IntegerField(default=10000, verbose_name='sprint order'),
        ),
        migrations.AlterField(
            model_name='userstory',
            name='sprint_order',
            field=models.IntegerField(default=10000, verbose_name='sprint order'),
        ),
    ]
