# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('userstories', '0006_auto_20141014_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstory',
            name='external_reference',
            field=djorm_pgarray.fields.TextArrayField(dbtype='text', verbose_name='external reference'),
            preserve_default=True,
        ),
    ]
