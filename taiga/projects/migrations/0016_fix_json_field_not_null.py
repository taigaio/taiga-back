# -*- coding: utf-8 -*-
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
