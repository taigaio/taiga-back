# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import django_pgjson.fields
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0019_auto_20150311_0821'),
        ('contenttypes', '0001_initial'),
        ('timeline', '0001_initial'),
        ('users', '0010_auto_20150414_0936'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Timeline',
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField()),
                ('namespace', models.SlugField(default='default')),
                ('event_type', models.SlugField()),
                ('project', models.ForeignKey(to='projects.Project')),
                ('data', django_pgjson.fields.JsonField()),
                ('data_content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='data_timelines')),
                ('created', models.DateTimeField(default=timezone.now)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', related_name='content_type_timelines')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='timeline',
            index_together=set([('content_type', 'object_id', 'namespace')]),
        ),
    ]
