# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_auto_20150114_0954'),
        ('issues', '0004_auto_20150114_0954'),
        ('userstories', '0009_remove_userstory_is_archived'),
        ('custom_attributes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueCustomAttributesValues',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('attributes_values', django_pgjson.fields.JsonField(default={}, verbose_name='attributes_values')),
                ('issue', models.OneToOneField(verbose_name='issue', to='issues.Issue', related_name='custom_attributes_values')),
            ],
            options={
                'verbose_name_plural': 'issue custom attributes values',
                'ordering': ['id'],
                'verbose_name': 'issue ustom attributes values',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskCustomAttributesValues',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('attributes_values', django_pgjson.fields.JsonField(default={}, verbose_name='attributes_values')),
                ('task', models.OneToOneField(verbose_name='task', to='tasks.Task', related_name='custom_attributes_values')),
            ],
            options={
                'verbose_name_plural': 'task custom attributes values',
                'ordering': ['id'],
                'verbose_name': 'task ustom attributes values',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStoryCustomAttributesValues',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('version', models.IntegerField(default=1, verbose_name='version')),
                ('attributes_values', django_pgjson.fields.JsonField(default={}, verbose_name='attributes_values')),
                ('user_story', models.OneToOneField(verbose_name='user story', to='userstories.UserStory', related_name='custom_attributes_values')),
            ],
            options={
                'verbose_name_plural': 'user story custom attributes values',
                'ordering': ['id'],
                'verbose_name': 'user story ustom attributes values',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
