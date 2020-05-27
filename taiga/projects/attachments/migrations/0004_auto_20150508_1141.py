# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0003_auto_20150114_0954'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='owner',
            field=models.ForeignKey(verbose_name='owner', blank=True, related_name='change_attachments', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
