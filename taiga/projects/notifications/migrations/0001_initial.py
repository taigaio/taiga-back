# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0002_auto_20140903_0920'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotifyPolicy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('notify_level', models.SmallIntegerField(choices=[(1, 'Not watching'), (2, 'Watching'), (3, 'Ignoring')])),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modified_at', models.DateTimeField()),
                ('project', models.ForeignKey(to='projects.Project', related_name='notify_policies', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='notify_policies', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['created_at'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='notifypolicy',
            unique_together=set([('project', 'user')]),
        ),
    ]
