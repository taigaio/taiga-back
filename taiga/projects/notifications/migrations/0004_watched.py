# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def fill_watched_table(apps, schema_editor):
    Watched = apps.get_model("notifications", "Watched")
    print("test")

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('notifications', '0003_auto_20141029_1143'),
    ]

    operations = [
        migrations.CreateModel(
            name='Watched',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created_date', models.DateTimeField(verbose_name='created date', auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='watched', verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(fill_watched_table),
    ]
