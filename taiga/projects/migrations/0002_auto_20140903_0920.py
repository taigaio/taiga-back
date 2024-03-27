# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import taiga.base.db.models.fields
import django.db.models.deletion
import taiga.projects.history.models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueStatus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('is_closed', models.BooleanField(verbose_name='is closed', default=False)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('project', models.ForeignKey(related_name='issue_statuses', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'issue statuses',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'issue status',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueType',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('project', models.ForeignKey(related_name='issue_types', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'issue types',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'issue type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Points',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('value', models.FloatField(blank=True, null=True, verbose_name='value', default=None)),
                ('project', models.ForeignKey(related_name='points', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'points',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'points',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('project', models.ForeignKey(related_name='priorities', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'priorities',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'priority',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectTemplate',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=250, verbose_name='name')),
                ('slug', models.SlugField(max_length=250, blank=True, verbose_name='slug', unique=True)),
                ('description', models.TextField(verbose_name='description')),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('default_owner_role', models.CharField(max_length=50, verbose_name="default owner's role")),
                ('is_backlog_activated', models.BooleanField(verbose_name='active backlog panel', default=True)),
                ('is_kanban_activated', models.BooleanField(verbose_name='active kanban panel', default=False)),
                ('is_wiki_activated', models.BooleanField(verbose_name='active wiki panel', default=True)),
                ('is_issues_activated', models.BooleanField(verbose_name='active issues panel', default=True)),
                ('videoconferences', models.CharField(max_length=250, null=True, choices=[('appear-in', 'AppearIn'), ('talky', 'Talky')], verbose_name='videoconference system', blank=True)),
                ('videoconferences_salt', models.CharField(max_length=250, null=True, verbose_name='videoconference room salt', blank=True)),
                ('default_options', taiga.base.db.models.fields.JSONField(null=True, verbose_name='default options', blank=True)),
                ('us_statuses', taiga.base.db.models.fields.JSONField(null=True, verbose_name='us statuses', blank=True)),
                ('points', taiga.base.db.models.fields.JSONField(null=True, verbose_name='points', blank=True)),
                ('task_statuses', taiga.base.db.models.fields.JSONField(null=True, verbose_name='task statuses', blank=True)),
                ('issue_statuses', taiga.base.db.models.fields.JSONField(null=True, verbose_name='issue statuses', blank=True)),
                ('issue_types', taiga.base.db.models.fields.JSONField(null=True, verbose_name='issue types', blank=True)),
                ('priorities', taiga.base.db.models.fields.JSONField(null=True, verbose_name='priorities', blank=True)),
                ('severities', taiga.base.db.models.fields.JSONField(null=True, verbose_name='severities', blank=True)),
                ('roles', taiga.base.db.models.fields.JSONField(null=True, verbose_name='roles', blank=True)),
            ],
            options={
                'verbose_name_plural': 'project templates',
                'verbose_name': 'project template',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Severity',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('project', models.ForeignKey(related_name='severities', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'severities',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'severity',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskStatus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('is_closed', models.BooleanField(verbose_name='is closed', default=False)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('project', models.ForeignKey(related_name='task_statuses', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'task statuses',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'task status',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStoryStatus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('order', models.IntegerField(verbose_name='order', default=10)),
                ('is_closed', models.BooleanField(verbose_name='is closed', default=False)),
                ('color', models.CharField(max_length=20, verbose_name='color', default='#999999')),
                ('wip_limit', models.IntegerField(blank=True, null=True, verbose_name='work in progress limit', default=None)),
                ('project', models.ForeignKey(related_name='us_statuses', to='projects.Project', verbose_name='project', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'user story statuses',
                'ordering': ['project', 'order', 'name'],
                'verbose_name': 'user story status',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userstorystatus',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='taskstatus',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='severity',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='priority',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='points',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='issuetype',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='issuestatus',
            unique_together=set([('project', 'name')]),
        ),
        migrations.AddField(
            model_name='project',
            name='creation_template',
            field=models.ForeignKey(null=True, related_name='projects', default=None, blank=True, to='projects.ProjectTemplate', verbose_name='creation template', on_delete=models.SET_NULL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_issue_status',
            field=models.OneToOneField(to='projects.IssueStatus', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default issue status'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_issue_type',
            field=models.OneToOneField(to='projects.IssueType', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default issue type'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_points',
            field=models.OneToOneField(to='projects.Points', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default points'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_priority',
            field=models.OneToOneField(to='projects.Priority', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default priority'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_severity',
            field=models.OneToOneField(to='projects.Severity', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default severity'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_task_status',
            field=models.OneToOneField(to='projects.TaskStatus', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default task status'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='project',
            name='default_us_status',
            field=models.OneToOneField(to='projects.UserStoryStatus', null=True, related_name='+', blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='default US status'),
            preserve_default=True,
        ),
    ]
