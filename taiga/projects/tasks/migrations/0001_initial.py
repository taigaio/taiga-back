# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20140903_0920'),
        ('milestones', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userstories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('tags', djorm_pgarray.fields.TextArrayField(dbtype='text', verbose_name='tags')),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('is_blocked', models.BooleanField(verbose_name='is blocked', default=False)),
                ('blocked_note', models.TextField(blank=True, verbose_name='blocked note', default='')),
                ('ref', models.BigIntegerField(null=True, blank=True, verbose_name='ref', db_index=True, default=None)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('finished_date', models.DateTimeField(null=True, blank=True, verbose_name='finished date')),
                ('subject', models.TextField(verbose_name='subject')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('is_iocaine', models.BooleanField(verbose_name='is iocaine', default=False)),
                ('assigned_to', models.ForeignKey(null=True, verbose_name='assigned to', default=None, blank=True, to=settings.AUTH_USER_MODEL, related_name='tasks_assigned_to_me')),
                ('milestone', models.ForeignKey(null=True, verbose_name='milestone', default=None, blank=True, to='milestones.Milestone', related_name='tasks')),
                ('owner', models.ForeignKey(null=True, verbose_name='owner', default=None, blank=True, to=settings.AUTH_USER_MODEL, related_name='owned_tasks')),
                ('project', models.ForeignKey(verbose_name='project', to='projects.Project', related_name='tasks')),
                ('status', models.ForeignKey(verbose_name='status', to='projects.TaskStatus', related_name='tasks')),
                ('user_story', models.ForeignKey(null=True, verbose_name='user story', blank=True, to='userstories.UserStory', related_name='tasks')),
                ('watchers', models.ManyToManyField(null=True, blank=True, to=settings.AUTH_USER_MODEL, verbose_name='watchers', related_name='tasks_task+')),
            ],
            options={
                'verbose_name_plural': 'tasks',
                'ordering': ['project', 'created_date'],
                'verbose_name': 'task',
                'permissions': (('view_task', 'Can view task'),),
            },
            bases=(models.Model,),
        ),
    ]
