# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0003_auto_20150114_0954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='owner',
            field=models.ForeignKey(verbose_name='owner', blank=True, related_name='change_attachments', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
