# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
