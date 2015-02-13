# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0002_issuecustomattributesvalues_taskcustomattributesvalues_userstorycustomattributesvalues'),
    ]

    operations = [
        # Function: Remove a key in a json field
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION "json_object_delete_keys"("json" json, VARIADIC "keys_to_delete" text[])
                               RETURNS json
                              LANGUAGE sql
                             IMMUTABLE
                                STRICT
                                    AS $function$
                       SELECT COALESCE ((SELECT ('{' || string_agg(to_json("key") || ':' || "value", ',') || '}')
                                           FROM json_each("json")
                                          WHERE "key" <> ALL ("keys_to_delete")),
                                        '{}')::json $function$;
            """,
            reverse_sql="""DROP FUNCTION IF EXISTS "json_object_delete_keys";"""
        ),

        # Function: Romeve a key in the json field of *_custom_attributes_values.values
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION "clean_key_in_custom_attributes_values"()
                               RETURNS trigger
                                    AS $clean_key_in_custom_attributes_values$
                               DECLARE
                                       key text;
                                       tablename text;
                                 BEGIN
                                       key := OLD.id::text;
                                       tablename := TG_ARGV[0]::text;

                                     EXECUTE 'UPDATE ' || quote_ident(tablename) || '
                                                 SET values = json_object_delete_keys(values, ' || quote_literal(key) || ')';

                                       RETURN NULL;
                                   END; $clean_key_in_custom_attributes_values$
                              LANGUAGE plpgsql;

            """,
            reverse_sql="""DROP FUNCTION IF EXISTS "clean_key_in_custom_attributes_values";"""
        ),

        # Trigger: Clean userstorycustomattributes values before remove a userstorycustomattribute
        migrations.RunSQL(
            """
            CREATE TRIGGER "update_userstorycustomvalues_afeter_remove_userstorycustomattribute"
          BEFORE DELETE ON custom_attributes_userstorycustomattribute
              FOR EACH ROW
         EXECUTE PROCEDURE clean_key_in_custom_attributes_values('custom_attributes_userstorycustomattributesvalues');
            """,
            reverse_sql="""DROP TRIGGER "update_userstorycustomvalues_afeter_remove_userstorycustomattribute";"""
        ),

        # Trigger: Clean taskcustomattributes values before remove a taskcustomattribute
        migrations.RunSQL(
            """
            CREATE TRIGGER "update_taskcustomvalues_afeter_remove_taskcustomattribute"
          BEFORE DELETE ON custom_attributes_taskcustomattribute
              FOR EACH ROW
         EXECUTE PROCEDURE clean_key_in_custom_attributes_values('custom_attributes_taskcustomattributesvalues');
            """,
            reverse_sql="""DROP TRIGGER "update_taskcustomvalues_afeter_remove_taskcustomattribute";"""
        ),

        # Trigger: Clean issuecustomattributes values before remove a issuecustomattribute
        migrations.RunSQL(
            """
            CREATE TRIGGER "update_issuecustomvalues_afeter_remove_issuecustomattribute"
          BEFORE DELETE ON custom_attributes_issuecustomattribute
              FOR EACH ROW
         EXECUTE PROCEDURE clean_key_in_custom_attributes_values('custom_attributes_issuecustomattributesvalues');
            """,
            reverse_sql="""DROP TRIGGER "update_issuecustomvalues_afeter_remove_issuecustomattribute";"""
        )
    ]
