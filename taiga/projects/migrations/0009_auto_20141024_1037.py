# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20141024_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuestatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='taskstatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='userstorystatus',
            name='slug',
            field=models.SlugField(verbose_name='slug', blank=True, max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='issuestatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='taskstatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='userstorystatus',
            unique_together=set([('project', 'name'), ('project', 'slug')]),
        ),
    ]
