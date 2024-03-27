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
        ('custom_attributes', '0006_auto_20151014_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuecustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
        migrations.AlterField(
            model_name='taskcustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
        migrations.AlterField(
            model_name='userstorycustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
    ]
