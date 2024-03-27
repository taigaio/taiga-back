# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0004_auto_20141001_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstory',
            name='generated_from_issue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='issues.Issue', verbose_name='generated from issue', related_name='generated_user_stories', null=True),
        ),
    ]
