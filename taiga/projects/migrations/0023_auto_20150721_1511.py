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
        ('projects', '0022_auto_20150701_0924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='videoconferences_extra_data',
            field=models.CharField(max_length=250, blank=True, null=True, verbose_name='videoconference extra data'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='projecttemplate',
            name='videoconferences_extra_data',
            field=models.CharField(max_length=250, blank=True, null=True, verbose_name='videoconference extra data'),
            preserve_default=True,
        ),
    ]
