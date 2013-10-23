# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from greenmine.projects.admin import AttachmentInline
from . import models



class TaskAdmin(reversion.VersionAdmin):
    list_display = ["subject", "ref", "user_story", "milestone", "project", "user_story_id"]
    list_filter = ["project"]
    list_display_links = list_display
    readonly_fields = ["project", "milestone", "user_story", "status", "owner", "assigned_to"]
    inlines = [AttachmentInline]

    def user_story_id(self, instance):
        return instance.user_story.id

admin.site.register(models.Task, TaskAdmin)
