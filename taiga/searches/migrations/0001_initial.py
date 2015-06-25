# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),
        ('userstories', '0009_remove_userstory_is_archived'),
        ('issues', '0005_auto_20150623_1923'),
        ('tasks', '0006_auto_20150623_1923'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE INDEX "userstories_full_text_idx" ON userstories_userstory USING gin(to_tsvector('simple', coalesce(subject, '') || ' ' || coalesce(ref) || ' ' || coalesce(description, '')));
            """,
            reverse_sql="""DROP INDEX IF EXISTS "userstories_full_text_idx";"""
        ),
        migrations.RunSQL(
            """
            CREATE INDEX "tasks_full_text_idx" ON tasks_task USING gin(to_tsvector('simple', coalesce(subject, '') || ' ' || coalesce(ref) || ' ' || coalesce(description, '')));
            """,
            reverse_sql="""DROP INDEX IF EXISTS "tasks_full_text_idx";"""
        ),
        migrations.RunSQL(
            """
            CREATE INDEX "issues_full_text_idx" ON issues_issue USING gin(to_tsvector('simple', coalesce(subject, '') || ' ' || coalesce(ref) || ' ' || coalesce(description, '')));
            """,
            reverse_sql="""DROP INDEX IF EXISTS "issues_full_text_idx";"""
        ),
        migrations.RunSQL(
            """
            CREATE INDEX "wikipages_full_text_idx" ON wiki_wikipage USING gin(to_tsvector('simple', coalesce(slug, '') || ' ' || coalesce(content, '')));
            """,
            reverse_sql="""DROP INDEX IF EXISTS "wikipages_full_text_idx";"""
        ),
    ]
