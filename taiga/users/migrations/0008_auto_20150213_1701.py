# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20150209_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authdata',
            name='user',
            field=models.ForeignKey(related_name='auth_data', to=settings.AUTH_USER_MODEL),
        ),
    ]
