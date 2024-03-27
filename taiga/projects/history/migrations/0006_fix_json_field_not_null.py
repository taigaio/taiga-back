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
        ('history', '0005_auto_20141120_1119'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE history_historyentry ALTER COLUMN "user" DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE history_historyentry ALTER COLUMN "diff" DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE history_historyentry ALTER COLUMN "snapshot" DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE history_historyentry ALTER COLUMN "values" DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE history_historyentry ALTER COLUMN "delete_comment_user" DROP NOT NULL;',
        ),
    ]
