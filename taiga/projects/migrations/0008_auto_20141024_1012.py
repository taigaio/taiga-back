# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from unidecode import unidecode

from django.db import models, migrations
from django.template.defaultfilters import slugify

from taiga.projects.models import UserStoryStatus, TaskStatus, IssueStatus

def update_many(objects, fields=[], using="default"):
    """Update list of Django objects in one SQL query, optionally only
    overwrite the given fields (as names, e.g. fields=["foo"]).
    Objects must be of the same Django model. Note that save is not
    called and signals on the model are not raised."""
    if not objects:
        return

    import django.db.models
    from django.db import connections
    con = connections[using]

    names = fields
    meta = objects[0]._meta
    fields = [f for f in meta.fields if not isinstance(f, django.db.models.AutoField) and (not names or f.name in names)]

    if not fields:
        raise ValueError("No fields to update, field names are %s." % names)

    fields_with_pk = fields + [meta.pk]
    parameters = []
    for o in objects:
        parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields_with_pk))

    table = meta.db_table
    assignments = ",".join(("%s=%%s"% con.ops.quote_name(f.column)) for f in fields)
    con.cursor().executemany(
        "update %s set %s where %s=%%s" % (table, assignments, con.ops.quote_name(meta.pk.column)),
        parameters)


def update_slug(apps, schema_editor):
    update_qs = UserStoryStatus.objects.all().only("name")
    for us_status in update_qs:
        us_status.slug = slugify(unidecode(us_status.name))

    update_many(update_qs, fields=["slug"])

    update_qs = TaskStatus.objects.all().only("name")
    for task_status in update_qs:
        task_status.slug = slugify(unidecode(task_status.name))

    update_many(update_qs, fields=["slug"])

    update_qs = IssueStatus.objects.all().only("name")
    for issue_status in update_qs:
        issue_status.slug = slugify(unidecode(issue_status.name))

    update_many(update_qs, fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_auto_20141024_1011'),
    ]

    operations = [
        migrations.RunPython(update_slug)
    ]
