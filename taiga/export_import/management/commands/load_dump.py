# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from optparse import make_option

from taiga.base.utils import json
from taiga.projects.models import Project
from taiga.export_import.renderers import ExportRenderer
from taiga.export_import.dump_service import dict_to_project, TaigaImportError
from taiga.export_import.service import get_errors


class Command(BaseCommand):
    args = '<dump_file> <owner-email>'
    help = 'Export a project to json'
    renderer_context = {"indent": 4}
    renderer = ExportRenderer()
    option_list = BaseCommand.option_list + (
        make_option('--overwrite',
                    action='store_true',
                    dest='overwrite',
                    default=False,
                    help='Delete project if exists'),
        )

    def handle(self, *args, **options):
        data = json.loads(open(args[0], 'r').read())
        try:
            with transaction.atomic():
                if options["overwrite"]:
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
                dict_to_project(data, args[1])
        except TaigaImportError as e:
            print("ERROR:", end=" ")
            print(e.message)
            print(get_errors())
