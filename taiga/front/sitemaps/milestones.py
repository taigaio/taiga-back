# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db.models import Q
from django.apps import apps
from datetime import timedelta
from django.utils import timezone

from taiga.front.templatetags.functions import resolve

from .base import Sitemap


class MilestonesSitemap(Sitemap):
    def items(self):
        milestone_model = apps.get_model("milestones", "Milestone")

        # Get US of public projects OR private projects if anon user can view them and us and tasks
        queryset = milestone_model.objects.filter(Q(project__is_private=False) |
                                                  Q(project__is_private=True,
                                                    project__anon_permissions__contains=["view_milestones",
                                                                                         "view_us",
                                                                                         "view_tasks"]))

        queryset = queryset.exclude(name="")

        # Exclude blocked projects
        queryset = queryset.filter(project__blocked_code__isnull=True)

        # Project data is needed
        queryset = queryset.select_related("project")

        return queryset

    def location(self, obj):
        return resolve("taskboard", obj.project.slug, obj.slug)

    def lastmod(self, obj):
        return obj.modified_date

    def changefreq(self, obj):
        if (timezone.now() - obj.modified_date) > timedelta(days=90):
            return "monthly"
        return "weekly"

    def priority(self, obj):
        return 0.1
