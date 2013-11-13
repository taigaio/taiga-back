# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.contenttypes import generic

from greenmine.projects.milestones.admin import MilestoneInline
from . import models

import reversion


class AttachmentAdmin(reversion.VersionAdmin):
    list_display = ["id", "project", "attached_file", "owner", "content_type", "content_object"]
    list_display_links = ["id", "attached_file",]
    list_filter = ["project", "content_type"]


class AttachmentInline(generic.GenericTabularInline):
     model = models.Attachment
     fields = ("attached_file", "owner")
     extra = 0


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_display_links = list_display
    list_filter = ['project', 'role']


class MembershipInline(admin.TabularInline):
    model = models.Membership
    extra = 0


class ProjectAdmin(reversion.VersionAdmin):
    list_display = ["name", "owner", "created_date", "total_milestones",
                    "total_story_points"]
    list_display_links = list_display
    inlines = [MembershipInline, MilestoneInline]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["default_points", "default_us_status", "default_task_status",
                              "default_priority", "default_severity",
                              "default_issue_status", "default_issue_type",
                              "default_question_status"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                                      project=self.obj.project)
        else:
            kwargs["queryset"] = db_field.related.parent_model.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# User Stories common admins

class PointsAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "value"]
    list_display_links = ["name"]
    list_filter = ["project"]


class UserStoryStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed"]
    list_display_links = ["name"]
    list_filter = ["project"]


# Tasks common admins

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]


# Issues common admins

class SeverityAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]


class PriorityAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]


# Questions common admins

class QuestionStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed", "color"]
    list_display_links = ["name"]
    list_filter = ["project"]



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

admin.site.register(models.QuestionStatus, QuestionStatusAdmin)
