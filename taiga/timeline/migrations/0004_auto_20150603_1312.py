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
        ('timeline', '0003_auto_20150410_0829'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeline',
            name='project',
            field=models.ForeignKey(null=True, to='projects.Project', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
