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
        ('projects', '0015_auto_20141230_1212'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE projects_projectmodulesconfig ALTER COLUMN config DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN default_options DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN us_statuses DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN points DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN task_statuses DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN issue_statuses DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN issue_types DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN priorities DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN severities DROP NOT NULL;',
        ),
        migrations.RunSQL(
            sql='ALTER TABLE projects_projecttemplate ALTER COLUMN roles DROP NOT NULL;',
        ),
    ]
