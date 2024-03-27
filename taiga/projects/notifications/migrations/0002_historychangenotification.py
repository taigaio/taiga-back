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
        ('projects', '0005_membership_invitation_extra_text'),
        ('history', '0004_historyentry_is_hidden'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryChangeNotification',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('key', models.CharField(max_length=255, editable=False)),
                ('created_datetime', models.DateTimeField(verbose_name='created date time', auto_now_add=True)),
                ('updated_datetime', models.DateTimeField(verbose_name='updated date time', auto_now_add=True)),
                ('history_type', models.SmallIntegerField(choices=[(1, 'Change'), (2, 'Create'), (3, 'Delete')])),
                ('history_entries', models.ManyToManyField(blank=True, null=True, to='history.HistoryEntry', verbose_name='history entries', related_name='+')),
                ('notify_users', models.ManyToManyField(blank=True, null=True, to=settings.AUTH_USER_MODEL, verbose_name='notify users', related_name='+')),
                ('owner', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='owner', on_delete=models.CASCADE)),
                ('project', models.ForeignKey(related_name='+', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
