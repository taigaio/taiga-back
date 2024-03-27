# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import connection
from django.db import models, migrations
from django.contrib.contenttypes.models import ContentType
from taiga.base.utils.contenttypes import update_all_contenttypes

def create_notifications(apps, schema_editor):
    update_all_contenttypes(verbosity=0)
    sql="""
INSERT INTO notifications_watched (object_id, created_date, content_type_id, user_id, project_id)
SELECT userstory_id AS object_id, now() AS created_date, {content_type_id} AS content_type_id, user_id, project_id
FROM userstories_userstory_watchers INNER JOIN userstories_userstory ON userstories_userstory_watchers.userstory_id = userstories_userstory.id""".format(content_type_id=ContentType.objects.get(model='userstory').id)
    cursor = connection.cursor()
    cursor.execute(sql)


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_watched'),
        ('userstories', '0009_remove_userstory_is_archived'),
    ]

    operations = [
        migrations.RunPython(create_notifications),
        migrations.RemoveField(
            model_name='userstory',
            name='watchers',
        ),
    ]
