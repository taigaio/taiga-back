# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models

import reversion



class SeverityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.Severity, SeverityAdmin)


class PriorityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.Priority, PriorityAdmin)


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.IssueType, IssueTypeAdmin)


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.IssueStatus, IssueStatusAdmin)


class IssueAdmin(reversion.VersionAdmin):
    list_display = ["subject", "type"]

admin.site.register(models.Issue, IssueAdmin)
