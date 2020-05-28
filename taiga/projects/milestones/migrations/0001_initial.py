# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_auto_20140903_0920'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Milestone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=200, db_index=True)),
                ('slug', models.SlugField(verbose_name='slug', blank=True, max_length=250)),
                ('estimated_start', models.DateField(verbose_name='estimated start date')),
                ('estimated_finish', models.DateField(verbose_name='estimated finish date')),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('closed', models.BooleanField(verbose_name='is closed', default=False)),
                ('disponibility', models.FloatField(null=True, blank=True, verbose_name='disponibility', default=0.0)),
                ('order', models.PositiveSmallIntegerField(verbose_name='order', default=1)),
                ('owner', models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL, verbose_name='owner', related_name='owned_milestones', on_delete=models.SET_NULL)),
                ('project', models.ForeignKey(to='projects.Project', verbose_name='project', related_name='milestones', on_delete=models.CASCADE)),
                ('watchers', models.ManyToManyField(null=True, blank=True, related_name='milestones_milestone+', verbose_name='watchers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'milestone',
                'verbose_name_plural': 'milestones',
                'ordering': ['project', 'created_date'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='milestone',
            unique_together=set([('slug', 'project'), ('name', 'project')]),
        ),
    ]
