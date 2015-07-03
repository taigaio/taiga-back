# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.core.files import File

def update_gitlab_system_user_photo_to_v2(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias

    try:
        user = User.objects.using(db_alias).get(username__startswith="gitlab-",
                                                is_active=False,
                                                is_system=True)
        f = open("taiga/hooks/gitlab/migrations/logo-v2.png", "rb")
        user.photo.save("logo.png", File(f))
        user.save()
    except User.DoesNotExist:
        pass

def update_gitlab_system_user_photo_to_v1(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias

    try:
        user = User.objects.using(db_alias).get(username__startswith="gitlab-",
                                                is_active=False,
                                                is_system=True)
        f = open("taiga/hooks/gitlab/migrations/logo.png", "rb")
        user.photo.save("logo.png", File(f))
        user.save()
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('gitlab', '0001_initial'),
        ('users', '0011_user_theme'),
    ]

    operations = [
        migrations.RunPython(update_gitlab_system_user_photo_to_v2,
                             update_gitlab_system_user_photo_to_v1),
    ]
