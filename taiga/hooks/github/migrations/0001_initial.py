# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.core.files import File

import uuid


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
    f = open("taiga/hooks/github/migrations/logo.png", "rb")
    user.photo.save("logo.png", File(f))
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20141030_1132')
    ]

    operations = [
        migrations.RunPython(create_github_system_user),
    ]
