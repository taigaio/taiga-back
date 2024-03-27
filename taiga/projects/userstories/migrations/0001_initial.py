# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone
import django.contrib.postgres.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '__first__'),
        ('milestones', '__first__'),
        ('projects', '0002_auto_20140903_0920'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0003_auto_20140903_0925'),
    ]

    operations = [
        migrations.CreateModel(
            name='RolePoints',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('points', models.ForeignKey(verbose_name='points', to='projects.Points', related_name='role_points', on_delete=models.CASCADE)),
                ('role', models.ForeignKey(verbose_name='role', to='users.Role', related_name='role_points', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['user_story', 'role'],
                'verbose_name': 'role points',
                'verbose_name_plural': 'role points',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=list, null=True, size=None, verbose_name='tags')),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('is_blocked', models.BooleanField(default=False, verbose_name='is blocked')),
                ('blocked_note', models.TextField(default='', blank=True, verbose_name='blocked note')),
                ('ref', models.BigIntegerField(default=None, db_index=True, blank=True, null=True, verbose_name='ref')),
                ('is_closed', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False, verbose_name='archived')),
                ('order', models.PositiveSmallIntegerField(default=100, verbose_name='order')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('finish_date', models.DateTimeField(blank=True, null=True, verbose_name='finish date')),
                ('subject', models.TextField(verbose_name='subject')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('client_requirement', models.BooleanField(default=False, verbose_name='is client requirement')),
                ('team_requirement', models.BooleanField(default=False, verbose_name='is team requirement')),
                ('assigned_to', models.ForeignKey(null=True, verbose_name='assigned to', to=settings.AUTH_USER_MODEL, related_name='userstories_assigned_to_me', blank=True, default=None, on_delete=models.SET_NULL)),
                ('generated_from_issue', models.ForeignKey(blank=True, null=True, verbose_name='generated from issue', to='issues.Issue', related_name='generated_user_stories', on_delete=models.SET_NULL)),
                ('milestone', models.ForeignKey(null=True, verbose_name='milestone', to='milestones.Milestone', related_name='user_stories', blank=True, default=None, on_delete=models.SET_NULL)),
                ('owner', models.ForeignKey(blank=True, null=True, verbose_name='owner', to=settings.AUTH_USER_MODEL, related_name='owned_user_stories', on_delete=models.CASCADE)),
                ('points', models.ManyToManyField(through='userstories.RolePoints', related_name='userstories', to='projects.Points', verbose_name='points')),
                ('project', models.ForeignKey(verbose_name='project', to='projects.Project', related_name='user_stories', on_delete=models.CASCADE)),
                ('status', models.ForeignKey(blank=True, null=True, verbose_name='status', to='projects.UserStoryStatus', related_name='user_stories', on_delete=models.SET_NULL)),
                ('watchers', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='userstories_userstory+', blank=True, null=True, verbose_name='watchers')),
            ],
            options={
                'ordering': ['project', 'order', 'ref'],
                'verbose_name': 'user story',
                'verbose_name_plural': 'user stories',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='rolepoints',
            name='user_story',
            field=models.ForeignKey(verbose_name='user story', to='userstories.UserStory', related_name='role_points', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='rolepoints',
            unique_together=set([('user_story', 'role')]),
        ),
    ]
