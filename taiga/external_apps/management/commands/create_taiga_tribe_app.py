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
from taiga.external_apps.models import Application


class Command(BaseCommand):
    args = ''
    help = 'Create Taiga Tribe external app information'

    def handle(self, *args, **options):
        Application.objects.get_or_create(
            id="8836b290-9f45-11e5-958e-52540016141a",
            name="Taiga Tribe",
            icon_url="https://tribe.taiga.io/static/common/graphics/logo/reindeer-color.png",
            web="https://tribe.taiga.io",
            description="A task-based employment marketplace for software development.",
            next_url="https://tribe.taiga.io/taiga-integration",
        )
