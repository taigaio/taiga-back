# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from greenmine.projects.admin import AttachmentInline

from . import models



class RolePointsInline(admin.TabularInline):
    model = models.RolePoints
    sortable_field_name = 'role'
    readonly_fields = ["user_story", "role", "points"]
    can_delete = False
    extra = 0
    max_num = 0


class RolePointsAdmin(admin.ModelAdmin):
    list_display = ["user_story", "role", "points"]
    list_display_links = list_display
    list_filter = ["role", "user_story__project"]
    readonly_fields = ["user_story", "role", "points"]


class UserStoryAdmin(reversion.VersionAdmin):
    list_display = ["id", "ref", "milestone", "project", "owner", 'status', 'is_closed']
    list_filter = ["project"]
    list_display_links = list_display
    readonly_fields = ["status", "milestone"]
    inlines = [RolePointsInline, AttachmentInline]


admin.site.register(models.UserStory, UserStoryAdmin)
admin.site.register(models.RolePoints, RolePointsAdmin)
