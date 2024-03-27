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
        ('projects', '0019_auto_20150311_0821'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='user_order',
            field=models.IntegerField(default=10000, verbose_name='user order'),
            preserve_default=True,
        ),
    ]
