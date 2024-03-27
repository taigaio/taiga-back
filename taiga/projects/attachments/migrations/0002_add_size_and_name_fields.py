# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

import os.path as path
from django.db import models, migrations


def parse_filenames_and_sizes(apps, schema_editor):
    Attachment = apps.get_model("attachments", "Attachment")

    for item in Attachment.objects.all():
        try:
            item.size = item.attached_file.size
        except Exception as e:
            item.size = 0

        item.name = path.basename(item.attached_file.name)
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='name',
            field=models.CharField(default='', blank=True, max_length=500),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='size',
            field=models.IntegerField(editable=False, null=True, blank=True, default=None),
            preserve_default=True,
        ),
        migrations.RunPython(parse_filenames_and_sizes)
    ]
