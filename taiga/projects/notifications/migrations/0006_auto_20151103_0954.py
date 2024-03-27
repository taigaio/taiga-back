# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20151005_1357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifypolicy',
            name='notify_level',
            field=models.SmallIntegerField(choices=[(1, 'Involved'), (2, 'All'), (3, 'None')]),
        ),
    ]
