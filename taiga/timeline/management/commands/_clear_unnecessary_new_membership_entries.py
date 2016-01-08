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
from django.conf import settings
from django.core.management.base import BaseCommand
from django.test.utils import override_settings

from taiga.timeline.models import Timeline
from taiga.projects.models import Project

class Command(BaseCommand):
    help = 'Regenerate unnecessary new memberships entry lines'

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        removing_timeline_ids = []
        for t in Timeline.objects.filter(event_type="projects.membership.create").order_by("created"):
            print(t.created)
            if t.project.owner.id == t.data["user"].get("id", None):
                removing_timeline_ids.append(t.id)

        Timeline.objects.filter(id__in=removing_timeline_ids).delete()
