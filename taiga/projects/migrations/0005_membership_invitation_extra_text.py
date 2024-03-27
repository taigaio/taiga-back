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
        ('projects', '0004_auto_20141002_2337'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='invitation_extra_text',
            field=models.TextField(null=True, verbose_name='invitation extra text', blank=True),
            preserve_default=True,
        ),
    ]
