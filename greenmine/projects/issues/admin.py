# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.projects.admin import AttachmentInline

from . import models

import reversion


class IssueAdmin(reversion.VersionAdmin):
    list_display = ["subject", "type"]
    inlines = [AttachmentInline]

admin.site.register(models.Issue, IssueAdmin)
