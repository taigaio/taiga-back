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
        ('projects', '0035_project_blocked_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='transfer_token',
            field=models.CharField(max_length=255, default=None, blank=True, null=True, verbose_name='project transfer token'),
        ),
    ]
