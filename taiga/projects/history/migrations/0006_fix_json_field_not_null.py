# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_pgjson.fields import JsonField

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
