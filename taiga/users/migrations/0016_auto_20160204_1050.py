# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20160120_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='max_memberships_private_projects',
            field=models.IntegerField(default=settings.MAX_MEMBERSHIPS_PRIVATE_PROJECTS, blank=True, verbose_name='max number of memberships for each owned private project', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='max_memberships_public_projects',
            field=models.IntegerField(default=settings.MAX_MEMBERSHIPS_PUBLIC_PROJECTS, blank=True, verbose_name='max number of memberships for each owned public project', null=True),
        ),
    ]
