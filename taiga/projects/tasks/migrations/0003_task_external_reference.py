# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_tasks_order_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='external_reference',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(blank=False, null=False), blank=True, default=None, null=True, size=None, verbose_name='external reference'),
            preserve_default=True,
        ),
    ]
