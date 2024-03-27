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
        ('projects', '0017_fix_is_private_for_projects'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='issues_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='tasks_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='userstories_csv_uuid',
            field=models.CharField(editable=False, max_length=32, default=None, null=True, db_index=True, blank=True),
            preserve_default=True,
        ),
    ]
