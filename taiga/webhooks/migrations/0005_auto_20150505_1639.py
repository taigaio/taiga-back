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
        ('webhooks', '0004_auto_20150202_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webhooklog',
            name='duration',
            field=models.FloatField(verbose_name='duration', default=0),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='webhooklog',
            name='request_data',
            field=taiga.base.db.models.fields.JSONField(verbose_name='request data'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='webhooklog',
            name='request_headers',
            field=taiga.base.db.models.fields.JSONField(verbose_name='request headers', default=dict),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='webhooklog',
            name='response_data',
            field=models.TextField(verbose_name='response data'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='webhooklog',
            name='response_headers',
            field=taiga.base.db.models.fields.JSONField(verbose_name='response headers', default=dict),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='webhooklog',
            name='status',
            field=models.IntegerField(verbose_name='status code'),
            preserve_default=True,
        ),
    ]
