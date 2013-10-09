# -*- coding: utf-8 -*-

from django.contrib import admin
import reversion

from greenmine.projects.milestones.admin import MilestoneInline
from . import models



class AttachmentAdmin(reversion.VersionAdmin):
    list_display = ["id", "owner"]

admin.site.register(models.Attachment, AttachmentAdmin)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_filter = ['project', 'role']

admin.site.register(models.Membership, MembershipAdmin)


class MembershipInline(admin.TabularInline):
    model = models.Membership
    fields = ('user', 'project', 'role')
    extra = 0


class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner"]
    # FIXME: commented because on save it raise strange
    # error 500 (seems bug in django)
    # inlines = [MembershipInline, MilestoneInline]

admin.site.register(models.Project, ProjectAdmin)


# User Stories common admins

class PointsAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.Points, PointsAdmin)


class UserStoryStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.UserStoryStatus, UserStoryStatusAdmin)


# Tasks common admins

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.TaskStatus, TaskStatusAdmin)


# Issues common admins

class SeverityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.Severity, SeverityAdmin)


class PriorityAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.Priority, PriorityAdmin)


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "project"]

admin.site.register(models.IssueType, IssueTypeAdmin)


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.IssueStatus, IssueStatusAdmin)


# Questions common admins

class QuestionStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_closed", "project"]

admin.site.register(models.QuestionStatus, QuestionStatusAdmin)
