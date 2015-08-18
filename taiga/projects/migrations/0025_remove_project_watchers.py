# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import update_all_contenttypes

def create_notifications(apps, schema_editor):
    update_all_contenttypes() 
    migrations.RunSQL(sql="""
INSERT INTO notifications_watched (object_id, created_date, content_type_id, user_id)
SELECT project_id AS object_id, now() AS created_date, {content_type_id} AS content_type_id, user_id
FROM projects_project_watchers""".format(content_type_id=ContentType.objects.get(model='project').id))


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0004_watched'),
        ('projects', '0024_auto_20150810_1247'),
    ]

    operations = [
        migrations.RunPython(create_notifications),
        migrations.RemoveField(
            model_name='project',
            name='watchers',
        ),
    ]
