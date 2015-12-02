# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


DROP_INMUTABLE_ARRAY_TO_STRING_FUNCTION = """
    DROP FUNCTION IF EXISTS inmutable_array_to_string(text[]) CASCADE
"""


# NOTE: This function is needed by taiga.projects.filters.QFilter
CREATE_INMUTABLE_ARRAY_TO_STRING_FUNCTION = """
    CREATE OR REPLACE FUNCTION inmutable_array_to_string(text[])
                       RETURNS text
                      LANGUAGE sql
                     IMMUTABLE AS $$SELECT array_to_string($1, ' ', '')$$
"""


DROP_INDEX = """
    DROP INDEX IF EXISTS projects_project_textquery_idx;
"""


# NOTE: This index is needed by taiga.projects.filters.QFilter
CREATE_INDEX = """
    CREATE INDEX projects_project_textquery_idx
              ON projects_project
           USING gin((setweight(to_tsvector('english_nostop',
                                coalesce(projects_project.name, '')), 'A') ||
                      setweight(to_tsvector('english_nostop',
                                 coalesce(inmutable_array_to_string(projects_project.tags), '')), 'B') ||
                      setweight(to_tsvector('english_nostop',
                                coalesce(projects_project.description, '')), 'C')));
"""


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0032_auto_20151202_1151'),
    ]

    operations = [
        migrations.RunSQL([DROP_INMUTABLE_ARRAY_TO_STRING_FUNCTION, CREATE_INMUTABLE_ARRAY_TO_STRING_FUNCTION],
                          [DROP_INMUTABLE_ARRAY_TO_STRING_FUNCTION]),
        migrations.RunSQL([DROP_INDEX, CREATE_INDEX],
                          [DROP_INDEX]),
    ]
