# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.management import update_all_contenttypes

def create_notifications(apps, schema_editor):
    update_all_contenttypes() 
    migrations.RunSQL(sql="""
INSERT INTO notifications_watched (object_id, created_date, content_type_id, user_id)
SELECT issue_id AS object_id, now() AS created_date, {content_type_id} AS content_type_id, user_id
FROM issues_issue_watchers""".format(content_type_id=ContentType.objects.get(model='issue').id))


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_watched'),
        ('issues', '0005_auto_20150623_1923'),
    ]

    operations = [
        migrations.RunPython(create_notifications),
        migrations.RemoveField(
            model_name='issue',
            name='watchers',
        ),
    ]
