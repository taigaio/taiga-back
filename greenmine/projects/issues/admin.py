# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models

import reversion


class IssueAdmin(reversion.VersionAdmin):
    list_display = ["subject", "type"]

admin.site.register(models.Issue, IssueAdmin)
