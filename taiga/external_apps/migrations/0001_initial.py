# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import taiga.external_apps.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.CharField(serialize=False, unique=True, max_length=255, default=taiga.external_apps.models._generate_uuid, primary_key=True)),
                ('name', models.CharField(verbose_name='name', max_length=255)),
                ('icon_url', models.TextField(null=True, blank=True, verbose_name='Icon url')),
                ('web', models.CharField(null=True, blank=True, max_length=255, verbose_name='web')),
                ('description', models.TextField(null=True, blank=True, verbose_name='description')),
                ('next_url', models.TextField(verbose_name='Next url')),
                ('key', models.TextField(verbose_name='secret key for ciphering the application tokens')),
            ],
            options={
                'verbose_name_plural': 'applications',
                'verbose_name': 'application',
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApplicationToken',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('auth_code', models.CharField(null=True, blank=True, max_length=255, default=None)),
                ('token', models.CharField(null=True, blank=True, max_length=255, default=None)),
                ('state', models.CharField(null=True, blank=True, max_length=255, default='')),
                ('application', models.ForeignKey(verbose_name='application', related_name='application_tokens', to='external_apps.Application', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(verbose_name='user', related_name='application_tokens', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='applicationtoken',
            unique_together=set([('application', 'user')]),
        ),
    ]
