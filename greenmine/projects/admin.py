# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.contenttypes import generic

from greenmine.projects.milestones.admin import MilestoneInline
from . import models

import reversion


class AttachmentAdmin(reversion.VersionAdmin):
    list_display = ["project", "attached_file", "owner"]
    list_display_links = list_display
    list_filter = ["project"]


class AttachmentInline(generic.GenericTabularInline):
     model = models.Attachment
     fields = ("attached_file", "owner")
     extra = 0


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_filter = ['project', 'role']
    list_display_links = list_display
    list_filter = ["project"]


class MembershipInline(admin.TabularInline):
    model = models.Membership
    fields = ['user', 'project', 'role']
    readonly_fields = ["project", "role"]
    extra = 0
    max_num = 0
    can_delete = False


class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner", "created_date", "total_milestones", "total_story_points"]
    list_display_links = list_display
    inlines = [MembershipInline, MilestoneInline]


# User Stories common admins

class PointsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]
    list_display_links = list_display
    list_filter = ["project"]


class UserStoryStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]
    list_display_links = list_display
    list_filter = ["project"]


# Tasks common admins

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]
    list_display_links = list_display


# Issues common admins

class SeverityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]
    list_display_links = list_display


class PriorityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]
    list_display_links = list_display


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]
    list_display_links = list_display


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]
    list_display_links = list_display


admin.site.register(models.IssueStatus, IssueStatusAdmin)
admin.site.register(models.TaskStatus, TaskStatusAdmin)
admin.site.register(models.UserStoryStatus, UserStoryStatusAdmin)
admin.site.register(models.Points, PointsAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Membership, MembershipAdmin)
admin.site.register(models.Severity, SeverityAdmin)
admin.site.register(models.Priority, PriorityAdmin)
admin.site.register(models.IssueType, IssueTypeAdmin)

# Questions common admins

class QuestionStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]
    list_display_links = list_display

admin.site.register(models.QuestionStatus, QuestionStatusAdmin)
