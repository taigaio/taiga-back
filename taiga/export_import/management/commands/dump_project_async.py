# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.conf import settings

from taiga.projects.models import Project
from taiga.users.models import User
from taiga.permissions.services import is_project_admin
from taiga.export_import import tasks


class Command(BaseCommand):
    help = "Export projects to a json file"

    def add_arguments(self, parser):
        parser.add_argument("project_slugs",
                            nargs="+",
                            help="<project_slug project_slug ...>")

        parser.add_argument("-u", "--user",
                            action="store",
                            dest="user",
                            default="./",
                            metavar="DIR",
                            required=True,
                            help="Dump as user by email or username.")

        parser.add_argument("-f", "--format",
                            action="store",
                            dest="format",
                            default="plain",
                            metavar="[plain|gzip]",
                            help="Format to the output file plain json or gzipped json. ('plain' by default)")

    def handle(self, *args, **options):
        username_or_email = options["user"]
        dump_format = options["format"]
        project_slugs = options["project_slugs"]

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except Exception:
            raise CommandError("Error loading user".format(username_or_email))

        for project_slug in project_slugs:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise CommandError("Project '{}' does not exist".format(project_slug))

            if not is_project_admin(user, project):
                self.stderr.write(self.style.ERROR(
                    "ERROR: Not sending task because user '{}' doesn't have permissions to export '{}' project".format(
                        username_or_email,
                        project_slug
                    )
                ))
                continue

            task = tasks.dump_project.delay(user, project, dump_format)
            tasks.delete_project_dump.apply_async(
                (project.pk, project.slug, task.id, dump_format),
                countdown=settings.EXPORTS_TTL
            )
            print("-> Sent task for dump of project '{}' as user {}".format(project.name, username_or_email))
