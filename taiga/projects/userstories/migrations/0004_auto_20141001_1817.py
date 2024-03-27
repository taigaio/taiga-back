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
        ('userstories', '0003_userstory_order_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rolepoints',
            options={'verbose_name': 'role points', 'verbose_name_plural': 'role points', 'ordering': ['user_story', 'role']},
        ),
        migrations.AlterModelOptions(
            name='userstory',
            options={'verbose_name': 'user story', 'verbose_name_plural': 'user stories', 'ordering': ['project', 'backlog_order', 'ref']},
        ),
    ]
