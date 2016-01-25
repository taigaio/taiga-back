# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20160120_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='max_members_private_projects',
            field=models.IntegerField(default=settings.MAX_MEMBERS_PRIVATE_PROJECTS, blank=True, verbose_name='max number of memberships for each owned private project', null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='max_members_public_projects',
            field=models.IntegerField(default=settings.MAX_MEMBERS_PUBLIC_PROJECTS, blank=True, verbose_name='max number of memberships for each owned public project', null=True),
        ),
    ]
