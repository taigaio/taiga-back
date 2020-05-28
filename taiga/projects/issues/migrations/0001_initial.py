# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('milestones', '__first__'),
        ('projects', '0002_auto_20140903_0920'),
    ]

    operations = [
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), blank=True, default=list, null=True, size=None, verbose_name='tags')),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('is_blocked', models.BooleanField(default=False, verbose_name='is blocked')),
                ('blocked_note', models.TextField(blank=True, default='', verbose_name='blocked note')),
                ('ref', models.BigIntegerField(null=True, blank=True, db_index=True, default=None, verbose_name='ref')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('finished_date', models.DateTimeField(blank=True, null=True, verbose_name='finished date')),
                ('subject', models.TextField(verbose_name='subject')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, verbose_name='assigned to', to=settings.AUTH_USER_MODEL, default=None, related_name='issues_assigned_to_me', on_delete=models.SET_NULL)),
                ('milestone', models.ForeignKey(blank=True, null=True, verbose_name='milestone', to='milestones.Milestone', default=None, related_name='issues', on_delete=models.SET_NULL)),
                ('owner', models.ForeignKey(blank=True, null=True, verbose_name='owner', to=settings.AUTH_USER_MODEL, default=None, related_name='owned_issues', on_delete=models.SET_NULL)),
                ('priority', models.ForeignKey(verbose_name='priority', to='projects.Priority', related_name='issues', on_delete=models.SET_NULL)),
                ('project', models.ForeignKey(verbose_name='project', to='projects.Project', related_name='issues', on_delete=models.CASCADE)),
                ('severity', models.ForeignKey(verbose_name='severity', to='projects.Severity', related_name='issues', on_delete=models.SET_NULL)),
                ('status', models.ForeignKey(verbose_name='status', to='projects.IssueStatus', related_name='issues', on_delete=models.SET_NULL)),
                ('type', models.ForeignKey(verbose_name='type', to='projects.IssueType', related_name='issues', on_delete=models.SET_NULL)),
                ('watchers', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, null=True, related_name='issues_issue+', verbose_name='watchers')),
            ],
            options={
                'verbose_name_plural': 'issues',
                'ordering': ['project', '-created_date'],
                'verbose_name': 'issue',
            },
            bases=(models.Model,),
        ),
    ]
