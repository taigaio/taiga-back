# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import taiga.base.db.models.fields


def migrate_github_id(apps, schema_editor):
    AuthData = apps.get_model("users", "AuthData")
    User = apps.get_model("users", "User")
    for user in User.objects.all():
        if user.github_id:
            AuthData.objects.create(user=user, key="github", value=user.github_id, extra={})


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20141030_1132'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthData',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('key', models.SlugField()),
                ('value', models.CharField(max_length=300)),
                ('extra', taiga.base.db.models.fields.JSONField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='authdata',
            unique_together=set([('key', 'value')]),
        ),
        migrations.RunPython(migrate_github_id),
        migrations.RemoveField(
            model_name='user',
            name='github_id',
        ),
    ]
