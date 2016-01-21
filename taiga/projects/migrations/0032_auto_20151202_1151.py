# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0031_project_logo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'permissions': (('view_project', 'Can view project'),), 'ordering': ['name', 'id'], 'verbose_name': 'project', 'verbose_name_plural': 'projects'},
        ),
        migrations.AlterIndexTogether(
            name='project',
            index_together=set([('name', 'id')]),
        ),
    ]
