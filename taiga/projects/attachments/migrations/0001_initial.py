# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import taiga.projects.attachments.models
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0002_auto_20140903_0920'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='object id')),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('attached_file', models.FileField(verbose_name='attached file', upload_to=taiga.projects.attachments.models.get_attachment_file_path, blank=True, null=True, max_length=500)),
                ('is_deprecated', models.BooleanField(verbose_name='is deprecated', default=False)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('order', models.IntegerField(verbose_name='order', default=0)),
                ('content_type', models.ForeignKey(verbose_name='content type', to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('owner', models.ForeignKey(verbose_name='owner', null=True, related_name='change_attachments', to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)),
                ('project', models.ForeignKey(verbose_name='project', related_name='attachments', to='projects.Project', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['project', 'created_date'],
                'verbose_name': 'attachment',
                'verbose_name_plural': 'attachments',
            },
            bases=(models.Model,),
        ),
    ]
