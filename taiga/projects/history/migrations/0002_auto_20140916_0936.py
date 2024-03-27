# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historyentry',
            name='delete_comment_date',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='historyentry',
            name='delete_comment_user',
            field=models.ForeignKey(null=True, default=None, related_name='deleted_comments', to=settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
