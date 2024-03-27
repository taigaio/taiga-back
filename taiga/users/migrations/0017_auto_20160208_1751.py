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
        ('users', '0016_auto_20160204_1050'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'ordering': ['order', 'slug'], 'verbose_name': 'role', 'verbose_name_plural': 'roles'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['username'], 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
