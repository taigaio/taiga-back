# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0003_userstory_order_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rolepoints',
            options={'verbose_name': 'role points', 'verbose_name_plural': 'role points', 'ordering': ['user_story', 'role']},
        ),
        migrations.AlterModelOptions(
            name='userstory',
            options={'verbose_name': 'user story', 'verbose_name_plural': 'user stories', 'ordering': ['project', 'backlog_order', 'ref']},
        ),
    ]
