# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

"""
Data migration to anonymize history entries for users that have already
been cancelled. This is a retroactive fix for GDPR compliance (issue #96).
"""

from django.db import migrations


def anonymize_cancelled_users_history(apps, schema_editor):
    User = apps.get_model("users", "User")
    HistoryEntry = apps.get_model("history", "HistoryEntry")
    connection = schema_editor.connection

    cancelled_users = User.objects.filter(date_cancelled__isnull=False)

    for user in cancelled_users:
        anon_user = {"pk": user.pk, "name": "Deleted user"}

        # Anonymize 'user' field
        HistoryEntry.objects.filter(
            user__pk=user.pk
        ).update(
            user=anon_user,
            values_diff_cache=None
        )

        # Anonymize 'delete_comment_user' field
        HistoryEntry.objects.filter(
            delete_comment_user__pk=user.pk
        ).update(
            delete_comment_user=anon_user
        )

        # Anonymize user references inside 'comment_versions' JSONB arrays
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE history_historyentry
                SET comment_versions = (
                    SELECT jsonb_agg(
                        CASE
                            WHEN (elem->'user'->>'id')::int = %s
                            THEN jsonb_set(elem, '{user}', '{"id": null}'::jsonb)
                            ELSE elem
                        END
                    )
                    FROM jsonb_array_elements(comment_versions) AS elem
                )
                WHERE comment_versions IS NOT NULL
                  AND comment_versions::text LIKE %s
            """, [user.pk, '%"id": {}%'.format(user.pk)])


class Migration(migrations.Migration):

    dependencies = [
        ("history", "0014_json_to_jsonb"),
        ("users", "0033_auto_20211110_1526"),
    ]

    operations = [
        migrations.RunPython(
            anonymize_cancelled_users_history,
            migrations.RunPython.noop,  # Not reversible
        ),
    ]
