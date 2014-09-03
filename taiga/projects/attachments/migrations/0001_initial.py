# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taiga.projects.attachments.models
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0002_auto_20140903_0920'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='object id')),
                ('created_date', models.DateTimeField(verbose_name='created date', default=django.utils.timezone.now)),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('attached_file', models.FileField(verbose_name='attached file', upload_to=taiga.projects.attachments.models.get_attachment_file_path, blank=True, null=True, max_length=500)),
                ('is_deprecated', models.BooleanField(verbose_name='is deprecated', default=False)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('order', models.IntegerField(verbose_name='order', default=0)),
                ('content_type', models.ForeignKey(verbose_name='content type', to='contenttypes.ContentType')),
                ('owner', models.ForeignKey(verbose_name='owner', null=True, related_name='change_attachments', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(verbose_name='project', related_name='attachments', to='projects.Project')),
            ],
            options={
                'ordering': ['project', 'created_date'],
                'verbose_name': 'attachment',
                'permissions': (('view_attachment', 'Can view attachment'),),
                'verbose_name_plural': 'attachments',
            },
            bases=(models.Model,),
        ),
    ]
