# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_auto_20151005_1357'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='max_private_projects',
            field=models.IntegerField(null=True, verbose_name='max number of owned private projects', default=settings.MAX_PRIVATE_PROJECTS_PER_USER, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='max_public_projects',
            field=models.IntegerField(null=True, verbose_name='max number of owned public projects', default=settings.MAX_PUBLIC_PROJECTS_PER_USER, blank=True),
        ),
    ]
