# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20160204_1050'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'ordering': ['order', 'slug'], 'verbose_name': 'role', 'verbose_name_plural': 'roles'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['username'], 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
