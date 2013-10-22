# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.projects.admin import AttachmentInline

from . import models

import reversion


class QuestionAdmin(reversion.VersionAdmin):
    list_display = ["subject", "project", "owner"]
    inlines = [AttachmentInline]

admin.site.register(models.Question, QuestionAdmin)
