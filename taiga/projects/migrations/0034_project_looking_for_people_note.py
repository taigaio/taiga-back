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
        ('projects', '0033_text_search_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='looking_for_people_note',
            field=models.TextField(blank=True, verbose_name='loking for people note', default=''),
        ),
    ]
