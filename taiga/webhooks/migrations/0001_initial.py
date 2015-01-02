# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_auto_20141230_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='Webhook',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('url', models.URLField(verbose_name='URL')),
                ('key', models.TextField(verbose_name='secret key')),
                ('project', models.ForeignKey(related_name='webhooks', to='projects.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WebhookLog',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('url', models.URLField(verbose_name='URL')),
                ('status', models.IntegerField(verbose_name='Status code')),
                ('request_data', django_pgjson.fields.JsonField(verbose_name='Request data')),
                ('response_data', models.TextField(verbose_name='Response data')),
                ('webhook', models.ForeignKey(related_name='logs', to='webhooks.Webhook')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
