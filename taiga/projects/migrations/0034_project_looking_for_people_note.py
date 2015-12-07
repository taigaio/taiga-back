# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0033_text_search_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='looking_for_people_note',
            field=models.TextField(blank=True, verbose_name='loking for people note', default=''),
        ),
    ]
