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
        ('users', '0007_auto_20150209_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authdata',
            name='user',
            field=models.ForeignKey(related_name='auth_data', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
