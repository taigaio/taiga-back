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
        ('users', '0009_auto_20150326_1241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='lang',
            field=models.CharField(max_length=20, blank=True, null=True, default='', verbose_name='default language'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='timezone',
            field=models.CharField(max_length=20, blank=True, null=True, default='', verbose_name='default timezone'),
            preserve_default=True,
        ),
    ]
