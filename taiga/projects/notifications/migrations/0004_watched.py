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
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('notifications', '0003_auto_20141029_1143'),
    ]

    operations = [
        migrations.CreateModel(
            name='Watched',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created_date', models.DateTimeField(verbose_name='created date', auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='watched', verbose_name='user', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('project', models.ForeignKey(to='projects.Project', verbose_name='project', related_name='watched', on_delete=models.CASCADE)),

            ],
            options={
                'verbose_name': 'Watched',
                'verbose_name_plural': 'Watched',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='watched',
            unique_together=set([('content_type', 'object_id', 'user', 'project')]),
        ),
    ]
