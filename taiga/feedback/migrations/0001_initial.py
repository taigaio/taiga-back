# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('full_name', models.CharField(verbose_name='full name', max_length=256)),
                ('email', models.EmailField(verbose_name='email address', max_length=255)),
                ('comment', models.TextField(verbose_name='comment')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
            ],
            options={
                'verbose_name': 'feedback entry',
                'verbose_name_plural': 'feedback entries',
                'ordering': ['-created_date', 'id'],
            },
            bases=(models.Model,),
        ),
    ]
