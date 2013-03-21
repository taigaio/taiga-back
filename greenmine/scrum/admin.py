# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.scrum.models import Project, ProjectExtras, ProjectUserRole, \
    Milestone, UserStory, Change, ChangeAttachment, Task


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner"]

admin.site.register(Project, ProjectAdmin)


class ProjectExtrasAdmin(admin.ModelAdmin):
    list_display = ["project"]

admin.site.register(ProjectExtras, ProjectExtrasAdmin)


class ProjectUserRoleAdmin(admin.ModelAdmin):
    list_display = ["project", "user", "role"]

admin.site.register(ProjectUserRole, ProjectUserRoleAdmin)


class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "owner"]

admin.site.register(Milestone, MilestoneAdmin)


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ["ref", "milestone", "project", "owner"]

admin.site.register(UserStory, UserStoryAdmin)


class ChangeAdmin(admin.ModelAdmin):
    list_display = ["id", "change_type", "project", "owner"]

admin.site.register(Change, ChangeAdmin)


class ChangeAttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "change", "owner"]

admin.site.register(ChangeAttachment, ChangeAttachmentAdmin)


class TaskAdmin(admin.ModelAdmin):
    list_display = ["subject", "type", "user_story"]

admin.site.register(Task, TaskAdmin)
