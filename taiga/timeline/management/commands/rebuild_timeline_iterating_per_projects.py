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

from django.core.management.base import BaseCommand
from django.test.utils import override_settings
from django.core.management import call_command

from taiga.projects.models import Project


class Command(BaseCommand):
    help = 'Regenerate projects timeline iterating per project'

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        total = Project.objects.count()

        for count,project in enumerate(Project.objects.order_by("id")):
            print("""***********************************
 %s/%s %s
***********************************"""%(count+1, total, project.name))
            call_command("rebuild_timeline", project=project.id)
