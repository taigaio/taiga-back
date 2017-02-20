# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
