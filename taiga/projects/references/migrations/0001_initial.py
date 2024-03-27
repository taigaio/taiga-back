# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20140903_0920'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('ref', models.BigIntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('content_type', models.ForeignKey(related_name='+', to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('project', models.ForeignKey(related_name='references', to='projects.Project', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['created_at'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='reference',
            unique_together=set([('project', 'ref')]),
        ),
    ]
