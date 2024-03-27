# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from taiga.base.db.models.fields import JSONField

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userstorage', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE userstorage_storageentry ALTER COLUMN value DROP NOT NULL;',
        ),
    ]
