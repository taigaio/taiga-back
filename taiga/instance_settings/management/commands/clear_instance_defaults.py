# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from taiga.instance_settings.models import InstanceDefaults, InstanceDefaultsAudit


class Command(BaseCommand):
    help = "Clear instance language and theme overrides during operator recovery"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Confirm recovery reset")
        parser.add_argument("--actor", required=True, help="Instance superuser performing recovery")

    def handle(self, *args, **options):
        if not options["confirm"]:
            self.stderr.write("Pass --confirm to clear both instance defaults")
            return
        actor = get_user_model().objects.get(username=options["actor"], is_active=True,
                                             is_superuser=True)
        with transaction.atomic():
            defaults = InstanceDefaults.objects.select_for_update().get(pk=1)
            if defaults.default_language or defaults.default_theme:
                old_language, old_theme = defaults.default_language, defaults.default_theme
                defaults.default_language = ""
                defaults.default_theme = ""
                defaults.revision += 1
                defaults.save(update_fields=["default_language", "default_theme", "revision"])
                InstanceDefaultsAudit.objects.create(
                    actor=actor, old_language=old_language, new_language="",
                    old_theme=old_theme, new_theme="", revision=defaults.revision)
        self.stdout.write("Instance defaults cleared")
