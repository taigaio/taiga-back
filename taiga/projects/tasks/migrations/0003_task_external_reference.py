# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_tasks_order_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='external_reference',
            field=djorm_pgarray.fields.TextArrayField(dbtype='text', verbose_name='external reference'),
            preserve_default=True,
        ),
    ]
