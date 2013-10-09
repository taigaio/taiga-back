# -*- coding: utf-8 -*-

from django.contrib import admin

from .  import models

import reversion


class UserStoryInline(admin.TabularInline):
    model = models.UserStory
    fields = ('subject', 'order')
    sortable_field_name = 'order'
    extra = 0

    def get_inline_instances(self, request, obj=None):
        if obj:
            return obj.user_stories.filter(mileston__isnone=True)
        else:
            return models.UserStory.objects.none()


class RolePointsInline(admin.TabularInline):
    model = models.RolePoints
    sortable_field_name = 'role'
    extra = 0


class UserStoryAdmin(reversion.VersionAdmin):
    list_display = ["id", "ref", "milestone", "project", "owner", 'status', 'is_closed']
    list_filter = ["milestone", "project"]
    inlines = [RolePointsInline]

admin.site.register(models.UserStory, UserStoryAdmin)
