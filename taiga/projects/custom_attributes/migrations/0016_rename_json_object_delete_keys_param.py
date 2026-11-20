# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import migrations


# The helper functions created by migrations 0003, 0008 and 0011 name their
# first parameter "json". Since PostgreSQL 16 pg_dump writes that parameter
# without quotes and PostgreSQL 18 rejects it ("syntax error at or near json"),
# so a dump taken on an older server cannot be restored on a newer one.
# CREATE OR REPLACE cannot rename a parameter, so drop and recreate both
# overloads with a name that is not a keyword.

class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0015_auto_20200615_0811'),
    ]

    operations = [
        migrations.RunSQL(
            """
        DROP FUNCTION IF EXISTS "json_object_delete_keys"(json, VARIADIC text[]);
        DROP FUNCTION IF EXISTS "json_object_delete_keys"(jsonb, VARIADIC text[]);

        CREATE FUNCTION "json_object_delete_keys"("obj" json, VARIADIC "keys_to_delete" text[])
                           RETURNS json
                          LANGUAGE sql
                         IMMUTABLE
                            STRICT
                                AS $function$
                   SELECT COALESCE ((SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
                                       FROM json_each("obj")
                                      WHERE "key" <> ALL ("keys_to_delete")),
                                    '{}')::json $function$;

        CREATE FUNCTION "json_object_delete_keys"("obj" jsonb, VARIADIC "keys_to_delete" text[])
                           RETURNS jsonb
                          LANGUAGE sql
                         IMMUTABLE
                            STRICT
                                AS $function$
                   SELECT COALESCE ((SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
                                       FROM jsonb_each("obj")
                                      WHERE "key" <> ALL ("keys_to_delete")),
                                    '{}')::text::jsonb $function$;
            """,
            reverse_sql="""
        DROP FUNCTION IF EXISTS "json_object_delete_keys"(json, VARIADIC text[]);
        DROP FUNCTION IF EXISTS "json_object_delete_keys"(jsonb, VARIADIC text[]);

        CREATE FUNCTION "json_object_delete_keys"("json" json, VARIADIC "keys_to_delete" text[])
                           RETURNS json
                          LANGUAGE sql
                         IMMUTABLE
                            STRICT
                                AS $function$
                   SELECT COALESCE ((SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
                                       FROM json_each("json")
                                      WHERE "key" <> ALL ("keys_to_delete")),
                                    '{}')::json $function$;

        CREATE FUNCTION "json_object_delete_keys"("json" jsonb, VARIADIC "keys_to_delete" text[])
                           RETURNS jsonb
                          LANGUAGE sql
                         IMMUTABLE
                            STRICT
                                AS $function$
                   SELECT COALESCE ((SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
                                       FROM jsonb_each("json")
                                      WHERE "key" <> ALL ("keys_to_delete")),
                                    '{}')::text::jsonb $function$;
            """
        ),
    ]
