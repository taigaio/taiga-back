# -*- coding: utf-8 -*-
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
from django.core.management.base import CommandError
from django.test.utils import override_settings

from taiga.base.utils.slug import slugify_uniquely
from taiga.projects.models import Project
from taiga.projects.history.models import HistoryEntry
from taiga.timeline.management.commands.rebuild_timeline import generate_timeline


class Command(BaseCommand):
    help = 'Change the project slug from a new one'

    def add_arguments(self, parser):
        parser.add_argument('current_slug', help="The current project slug")
        parser.add_argument('new_slug', help="The new project slug")

    @override_settings(DEBUG=False)
    def handle(self, *args, **options):
        current_slug = options["current_slug"]
        new_slug = options["new_slug"]

        try:
            project = Project.objects.get(slug=current_slug)
        except Project.DoesNotExist:
            raise CommandError("There is no project with the slug '{}'".format(current_slug))

        slug = slugify_uniquely(new_slug, Project)
        if slug != new_slug:
            raise CommandError("Invalid new slug, maybe you can try with '{}'".format(slug))

        # Change slug
        self.stdout.write(self.style.SUCCESS("-> Change slug to '{}'.".format(slug)))
        project.slug = slug
        project.save()

        # Reset diff cache in history entries
        self.stdout.write(self.style.SUCCESS("-> Reset value_diff cache for history entries."))
        HistoryEntry.objects.filter(project=project).update(values_diff_cache=None)

        # Regenerate timeline
        self.stdout.write(self.style.SUCCESS("-> Regenerate timeline entries."))
        generate_timeline(None, None, project.id)
