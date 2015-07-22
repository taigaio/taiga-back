# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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
from taiga.export_import.renderers import ExportRenderer
from taiga.export_import.service import project_to_dict


class Command(BaseCommand):
    args = '<project_slug project_slug ...>'
    help = 'Export a project to json'
    renderer_context = {"indent": 4}
    renderer = ExportRenderer()

    def handle(self, *args, **options):
        for project_slug in args:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                raise CommandError('Project "%s" does not exist' % project_slug)

            data = project_to_dict(project)
            with open('%s.json'%(project_slug), 'w') as outfile:
                self.renderer.render_to_file(data, outfile, renderer_context=self.renderer_context)
