# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.files import File

import uuid
import os

CUR_DIR = os.path.dirname(__file__)


def create_gogs_system_user(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias

    if not User.objects.using(db_alias).filter(is_system=True, username__startswith="gogs-").exists():
        random_hash = uuid.uuid4().hex
        user = User.objects.using(db_alias).create(
            username="gogs-{}".format(random_hash),
            email="gogs-{}@taiga.io".format(random_hash),
            full_name="Gogs",
            is_active=False,
            is_system=True,
            bio="",
        )
        f = open("{}/logo.png".format(CUR_DIR), "rb")
        user.photo.save("logo.png", File(f))
        user.save()
        f.close()


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0010_auto_20150414_0936')
    ]

    operations = [
        migrations.RunPython(create_gogs_system_user),
    ]
