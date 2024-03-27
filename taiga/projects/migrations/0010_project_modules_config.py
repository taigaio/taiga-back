# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import taiga.base.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_auto_20141024_1037'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='modules_config',
            field=taiga.base.db.models.fields.JSONField(blank=True, null=True, verbose_name='modules config'),
            preserve_default=True,
        ),
    ]
