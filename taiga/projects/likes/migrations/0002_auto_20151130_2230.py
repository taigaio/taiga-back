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
        ('likes', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='likes',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='likes',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Likes',
        ),
    ]
