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

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import signals

from taiga.base.utils import json
from taiga.export_import import services
from taiga.export_import import exceptions as err
from taiga.projects.models import Project
from taiga.users.models import User


class Command(BaseCommand):
    help = 'Import a project from a json file'

    def add_arguments(self, parser):
        parser.add_argument("dump_file",
                            help="The path to a dump file (.json).")

        parser.add_argument("owner_email",
                            help="The email of the new project owner.")

        parser.add_argument("-o", '--overwrite',
                            action='store_true',
                            dest='overwrite',
                            default=False,
                            help='Overwrite the project if exists')

    def handle(self, *args, **options):
        dump_file_path = options["dump_file"]
        owner_email = options["owner_email"]
        overwrite = options["overwrite"]

        data = json.loads(open(dump_file_path, 'r').read())
        try:
            if overwrite:
                receivers_back = signals.post_delete.receivers
                signals.post_delete.receivers = []
                try:
                    proj = Project.objects.get(slug=data.get("slug", "not a slug"))
                    proj.tasks.all().delete()
                    proj.user_stories.all().delete()
                    proj.issues.all().delete()
                    proj.memberships.all().delete()
                    proj.roles.all().delete()
                    proj.delete()
                except Project.DoesNotExist:
                    pass
                signals.post_delete.receivers = receivers_back
            else:
                slug = data.get('slug', None)
                if slug is not None and Project.objects.filter(slug=slug).exists():
                    del data['slug']

            user = User.objects.get(email=owner_email)
            services.store_project_from_dict(data, user)
        except err.TaigaImportError as e:
            if e.project:
                e.project.delete_related_content()
                e.project.delete()

            print("ERROR:", end=" ")
            print(e.message)
            print(json.dumps(e.errors, indent=4))
