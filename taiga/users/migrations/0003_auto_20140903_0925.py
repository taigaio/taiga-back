# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        ('users', '0002_auto_20140903_0916'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='project',
            field=models.ForeignKey(related_name='roles', verbose_name='project', null=True, to='projects.Project'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='role',
            unique_together=set([('slug', 'project')]),
        ),
    ]
