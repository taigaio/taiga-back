# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.test.utils import override_settings

from taiga.base.utils.slug import slugify_uniquely
from taiga.projects.models import Project
from taiga.projects.history.models import HistoryEntry
from taiga.timeline.rebuilder import rebuild_timeline


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
        rebuild_timeline(None, None, project.id)
