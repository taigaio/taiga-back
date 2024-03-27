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
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='taskboard_order',
            field=models.IntegerField(default=1, verbose_name='taskboard order'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='task',
            name='us_order',
            field=models.IntegerField(default=1, verbose_name='us order'),
            preserve_default=True,
        ),
    ]
