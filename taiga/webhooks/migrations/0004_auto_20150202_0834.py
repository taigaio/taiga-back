# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0003_auto_20150122_1021'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='webhook',
            options={'ordering': ['name', '-id']},
        ),
        migrations.AlterModelOptions(
            name='webhooklog',
            options={'ordering': ['-created', '-id']},
        ),
    ]
