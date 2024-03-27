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
        ('projects', '0008_auto_20141024_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuestatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='taskstatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='userstorystatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='issuestatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='taskstatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='userstorystatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
    ]
