# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models

import reversion


class MilestoneInline(admin.TabularInline):
    model = models.Milestone
    fields = ('name', 'owner', 'estimated_start', 'estimated_finish', 'closed',
              'disponibility', 'order')
    sortable_field_name = 'order'
    extra = 0


class MilestoneAdmin(reversion.VersionAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start",
                    "estimated_finish"]

admin.site.register(models.Milestone, MilestoneAdmin)


