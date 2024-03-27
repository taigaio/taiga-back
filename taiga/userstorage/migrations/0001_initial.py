# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import taiga.base.db.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StorageEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date', auto_now=True)),
                ('key', models.CharField(max_length=255, verbose_name='key')),
                ('value', taiga.base.db.models.fields.JSONField(verbose_name='value', blank=True, default=None, null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='owner', related_name='storage_entries', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'storages entries',
                'verbose_name': 'storage entry',
                'ordering': ['owner', 'key'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='storageentry',
            unique_together=set([('owner', 'key')]),
        ),
    ]
