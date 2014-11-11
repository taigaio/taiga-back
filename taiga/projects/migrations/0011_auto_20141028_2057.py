# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_project_modules_config'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectModulesConfig',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('config', django_pgjson.fields.JsonField(null=True, verbose_name='modules config', blank=True)),
                ('project', models.OneToOneField(to='projects.Project', verbose_name='project', related_name='modules_config')),
            ],
            options={
                'verbose_name_plural': 'project modules configs',
                'verbose_name': 'project modules config',
                'ordering': ['project'],
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='project',
            name='modules_config',
        ),
    ]
