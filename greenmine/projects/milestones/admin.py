# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from . import models


class MilestoneInline(admin.TabularInline):
    model = models.Milestone

    fields = ['name', 'owner', 'estimated_start', 'estimated_finish', 'closed',
              'disponibility', 'order']
    readonly_fields = ["owner"]

    sortable_field_name = 'order'
    extra = 0
    max_num = 0
    can_delete = False


class MilestoneAdmin(reversion.VersionAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start",
                    "estimated_finish"]
    list_display_links = list_display
    list_filter = ["project"]
    readonly_fields = ["owner"]


admin.site.register(models.Milestone, MilestoneAdmin)
