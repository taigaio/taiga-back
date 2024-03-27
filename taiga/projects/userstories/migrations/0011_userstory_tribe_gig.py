# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import migrations, models
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0010_remove_userstory_watchers'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstory',
            name='tribe_gig',
            field=picklefield.fields.PickledObjectField(editable=False, null=True, default=None, verbose_name='taiga tribe gig', blank=True),
        ),
    ]
