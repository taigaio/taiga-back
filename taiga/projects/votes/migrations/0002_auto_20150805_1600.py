# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('votes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 8, 5, 16, 0, 40, 158374, tzinfo=utc), verbose_name='created date'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(related_name='votes', to=settings.AUTH_USER_MODEL, verbose_name='user'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='votes',
            name='count',
            field=models.PositiveIntegerField(default=0, verbose_name='count'),
            preserve_default=True,
        ),
    ]
