# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from __future__ import unicode_literals
import os.path
import uuid

from django.conf import settings
from django.core.files import File
from django.db import migrations


def create_github_system_user(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias
    random_hash = uuid.uuid4().hex
    user = User.objects.using(db_alias).create(
        username="github-{}".format(random_hash),
        email="github-{}@taiga.io".format(random_hash),
        full_name="GitHub",
        is_active=False,
        is_system=True,
        bio="",
    )
    f = open(os.path.join(settings.BASE_DIR, "taiga/hooks/github/migrations/logo.png"), "rb")
    user.photo.save("logo.png", File(f))
    user.save()
    f.close()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20141030_1132')
    ]

    operations = [
        migrations.RunPython(create_github_system_user),
    ]
