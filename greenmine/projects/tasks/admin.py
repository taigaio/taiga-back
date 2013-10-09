# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models

import reversion


class TaskAdmin(reversion.VersionAdmin):
    list_display = ["subject", "ref", "user_story", "milestone", "project", "user_story_id"]
    list_filter = ["user_story", "milestone", "project"]

    def user_story_id(self, instance):
        return instance.user_story.id

admin.site.register(models.Task, TaskAdmin)
