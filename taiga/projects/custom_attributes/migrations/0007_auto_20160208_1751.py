# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0006_auto_20151014_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuecustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
        migrations.AlterField(
            model_name='taskcustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
        migrations.AlterField(
            model_name='userstorycustomattribute',
            name='type',
            field=models.CharField(default='text', max_length=16, verbose_name='type', choices=[('text', 'Text'), ('multiline', 'Multi-Line Text'), ('date', 'Date'), ('url', 'Url')]),
        ),
    ]
