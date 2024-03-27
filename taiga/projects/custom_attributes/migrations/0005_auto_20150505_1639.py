# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
import taiga.base.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('custom_attributes', '0004_create_empty_customattributesvalues_for_existen_object'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuecustomattributesvalues',
            name='attributes_values',
            field=taiga.base.db.models.fields.JSONField(verbose_name='values', default=dict),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='taskcustomattributesvalues',
            name='attributes_values',
            field=taiga.base.db.models.fields.JSONField(verbose_name='values', default=dict),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='userstorycustomattributesvalues',
            name='attributes_values',
            field=taiga.base.db.models.fields.JSONField(verbose_name='values', default=dict),
            preserve_default=True,
        ),
    ]
