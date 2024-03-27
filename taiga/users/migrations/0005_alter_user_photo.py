# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import taiga.users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20140913_1914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.FileField(upload_to=taiga.users.models.get_user_file_path, blank=True, max_length=500, verbose_name='photo', null=True),
        ),
    ]
