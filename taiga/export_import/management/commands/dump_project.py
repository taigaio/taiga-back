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

from taiga.projects.models import Project
from taiga.export_import.services import render_project

import os
import gzip


class Command(BaseCommand):
    help = "Export projects to a json file"

    def add_arguments(self, parser):
        parser.add_argument("project_slugs",
                            nargs="+",
                            help="<project_slug project_slug ...>")

        parser.add_argument("-d", "--dst_dir",
                            action="store",
                            dest="dst_dir",
                            default="./",
                            metavar="DIR",
                            help="Directory to save the json files. ('./' by default)")

        parser.add_argument("-f", "--format",
                            action="store",
                            dest="format",
                            default="plain",
                            metavar="[plain|gzip]",
                            help="Format to the output file plain json or gzipped json. ('plain' by default)")

    def handle(self, *args, **options):
        dst_dir = options["dst_dir"]

        if not os.path.exists(dst_dir):
            raise CommandError("Directory {} does not exist.".format(dst_dir))

        if not os.path.isdir(dst_dir):
            raise CommandError("'{}' must be a directory, not a file.".format(dst_dir))

        project_slugs = options["project_slugs"]

        for project_slug in project_slugs:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise CommandError("Project '{}' does not exist".format(project_slug))

            if options["format"] == "gzip":
                dst_file = os.path.join(dst_dir, "{}.json.gz".format(project_slug))
                with gzip.GzipFile(dst_file, "wb") as f:
                    render_project(project, f)
            else:
                dst_file = os.path.join(dst_dir, "{}.json".format(project_slug))
                with open(dst_file, "wb") as f:
                    render_project(project, f)

            print("-> Generate dump of project '{}' in '{}'".format(project.name, dst_file))
