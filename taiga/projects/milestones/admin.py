# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin
from taiga.projects.notifications.admin import WatchedInline
from taiga.projects.votes.admin import VoteInline

from . import models


class MilestoneInline(admin.TabularInline):
    model = models.Milestone
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # Hack! Hook parent obj just in time to use in formfield_for_manytomany
        self.parent_obj = obj
        return super(MilestoneInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["owner"]):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__project=self.parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start",
                    "estimated_finish"]
    list_display_links = list_display
    readonly_fields = ["owner"]
    inlines = [WatchedInline, VoteInline]
    search_fields = ["name", "id"]
    raw_id_fields = ["project"]


admin.site.register(models.Milestone, MilestoneAdmin)
