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

# Examples:
# python manage.py rebuild_timeline --settings=settings.local_timeline --initial_date 2014-10-02 --final_date 2014-10-03
# python manage.py rebuild_timeline --settings=settings.local_timeline --purge
# python manage.py rebuild_timeline --settings=settings.local_timeline --initial_date 2014-10-02

from django.core.management.base import BaseCommand
from django.test.utils import override_settings

from taiga.timeline.models import Timeline
from taiga.timeline.rebuilder import rebuild_timeline

from optparse import make_option


class Command(BaseCommand):
    help = 'Regenerate project timeline'

    def add_arguments(self, parser):
        parser.add_argument('--purge',
                            action='store_true',
                            dest='purge',
                            default=False,
                            help='Purge existing timelines')
        parser.add_argument('--initial_date',
                            action='store',
                            dest='initial_date',
                            default=None,
                            help='Initial date for timeline generation')
        parser.add_argument('--final_date',
                            action='store',
                            dest='final_date',
                            default=None,
                            help='Final date for timeline generation')
        parser.add_argument('--project',
                            action='store',
                            dest='project',
                            default=None,
                            help='Selected project id for timeline generation')

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        if options["purge"] == True:
            Timeline.objects.all().delete()

        rebuild_timeline(options["initial_date"], options["final_date"], options["project"])
