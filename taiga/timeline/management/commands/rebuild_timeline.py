# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
