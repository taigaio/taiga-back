# -*- coding: utf-8 -*-

from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from greenmine.scrum import models
import reversion


class MilestoneInline(admin.TabularInline):
    model = models.Milestone
    fields = ('name', 'owner', 'estimated_start', 'estimated_finish', 'closed', 'disponibility', 'order')
    sortable_field_name = 'order'
    extra = 0


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

class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner"]
    inlines = [MilestoneInline, UserStoryInline]

admin.site.register(models.Project, ProjectAdmin)


class MilestoneAdmin(reversion.VersionAdmin):
    list_display = ["name", "project", "owner", "closed", "estimated_start", "estimated_finish"]

admin.site.register(models.Milestone, MilestoneAdmin)


class UserStoryAdmin(reversion.VersionAdmin):
    list_display = ["id", "ref", "milestone", "project", "owner", 'status', 'is_closed']
    list_filter = ["milestone", "project"]

admin.site.register(models.UserStory, UserStoryAdmin)


class ChangeAdmin(reversion.VersionAdmin):
    list_display = ["id", "change_type", "project", "owner"]

admin.site.register(models.Change, ChangeAdmin)


class ChangeAttachmentAdmin(reversion.VersionAdmin):
    list_display = ["id", "change", "owner"]

admin.site.register(models.ChangeAttachment, ChangeAttachmentAdmin)


class TaskAdmin(reversion.VersionAdmin):
    list_display = ["subject", "user_story", "milestone", "project", "user_story_id"]
    list_filter = ["user_story", "milestone", "project"]

    def user_story_id(self, instance):
        return instance.user_story.id


class IssueAdmin(reversion.VersionAdmin):
    list_display = ["subject", "type"]


class SeverityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

class PriorityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

class PointsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

class UserStoryStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.Task, TaskAdmin)
admin.site.register(models.Issue, IssueAdmin)

admin.site.register(models.Severity, SeverityAdmin)
admin.site.register(models.IssueStatus, IssueStatusAdmin)
admin.site.register(models.TaskStatus, TaskStatusAdmin)
admin.site.register(models.UserStoryStatus, UserStoryStatusAdmin)
admin.site.register(models.Priority, PriorityAdmin)
admin.site.register(models.IssueType, IssueTypeAdmin)
admin.site.register(models.Points, PointsAdmin)

