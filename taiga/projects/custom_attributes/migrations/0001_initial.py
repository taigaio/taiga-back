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
        ('projects', '0015_auto_20141230_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueCustomAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('order', models.IntegerField(verbose_name='order', default=10000)),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('project', models.ForeignKey(to='projects.Project', verbose_name='project', related_name='issuecustomattributes', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'issue custom attribute',
                'verbose_name_plural': 'issue custom attributes',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskCustomAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('order', models.IntegerField(verbose_name='order', default=10000)),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('project', models.ForeignKey(to='projects.Project', verbose_name='project', related_name='taskcustomattributes', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'task custom attribute',
                'verbose_name_plural': 'task custom attributes',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStoryCustomAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=64)),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('order', models.IntegerField(verbose_name='order', default=10000)),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('project', models.ForeignKey(to='projects.Project', verbose_name='project', related_name='userstorycustomattributes', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'user story custom attribute',
                'verbose_name_plural': 'user story custom attributes',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userstorycustomattribute',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='taskcustomattribute',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='issuecustomattribute',
            unique_together=set([('project', 'name')]),
        ),
    ]
