# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import connection
from django.db import migrations


def create_postgres_search_dictionary(apps, schema_editor):
    sql="""
CREATE TEXT SEARCH DICTIONARY english_stem_nostop (
    Template = snowball,
    Language = english
);
CREATE TEXT SEARCH CONFIGURATION public.english_nostop ( COPY = pg_catalog.english );
ALTER TEXT SEARCH CONFIGURATION public.english_nostop
ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, hword, hword_part, word WITH english_stem_nostop;
"""
    cursor = connection.cursor()
    cursor.execute(sql)

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0025_auto_20150901_1600'),
    ]

    operations = [
        migrations.RunPython(create_postgres_search_dictionary),
    ]
