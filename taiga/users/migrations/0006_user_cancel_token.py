# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='cancel_token',
            field=models.CharField(default=None, max_length=200, blank=True, null=True, verbose_name='email token'),
            preserve_default=True,
        ),
    ]
