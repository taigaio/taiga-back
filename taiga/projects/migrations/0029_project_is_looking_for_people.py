# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0028_project_is_featured'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='is_looking_for_people',
            field=models.BooleanField(verbose_name='is looking for people', default=False),
        ),
    ]
