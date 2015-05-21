# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0004_create_empty_customattributesvalues_for_existen_object'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuecustomattributesvalues',
            name='attributes_values',
            field=django_pgjson.fields.JsonField(verbose_name='values', default={}),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taskcustomattributesvalues',
            name='attributes_values',
            field=django_pgjson.fields.JsonField(verbose_name='values', default={}),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userstorycustomattributesvalues',
            name='attributes_values',
            field=django_pgjson.fields.JsonField(verbose_name='values', default={}),
            preserve_default=True,
        ),
    ]
