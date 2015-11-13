# Copyright (C) 2014-2015 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014-2015 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2015 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.contrib import admin

from taiga.projects.milestones.admin import MilestoneInline
from taiga.projects.notifications.admin import NotifyPolicyInline
from taiga.projects.likes.admin import LikeInline
from taiga.users.admin import RoleInline

from . import models

class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_display_links = list_display
    raw_id_fields = ["project"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["user", "invited_by"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                    memberships__project=self.obj.project)

        elif db_field.name in ["role"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                         project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class MembershipInline(admin.TabularInline):
    model = models.Membership
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # Hack! Hook parent obj just in time to use in formfield_for_manytomany
        self.parent_obj = obj
        return super(MembershipInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["user", "invited_by"]):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                         memberships__project=self.parent_obj)

        elif (db_field.name in ["role"]):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                                      project=self.parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_date", "total_milestones",
                    "total_story_points"]
    list_display_links = list_display
    inlines = [RoleInline, MembershipInline, MilestoneInline, NotifyPolicyInline, LikeInline]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["default_points", "default_us_status", "default_task_status",
                              "default_priority", "default_severity",
                              "default_issue_status", "default_issue_type"]):
            if getattr(self, 'obj', None):
                kwargs["queryset"] = db_field.related.model.objects.filter(
                                                          project=self.obj)
            else:
                kwargs["queryset"] = db_field.related.model.objects.none()

        elif (db_field.name in ["owner"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.model.objects.filter(
                                         memberships__project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                         memberships__project=self.obj)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# User Stories common admins

class PointsAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "value"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


class UserStoryStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


# Tasks common admins

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed", "color"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


# Issues common admins

class SeverityAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


class PriorityAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "color"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = ["project", "order", "name", "is_closed", "color"]
    list_display_links = ["name"]
    raw_id_fields = ["project"]


class ProjectTemplateAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.IssueStatus, IssueStatusAdmin)
admin.site.register(models.TaskStatus, TaskStatusAdmin)
admin.site.register(models.UserStoryStatus, UserStoryStatusAdmin)
admin.site.register(models.Points, PointsAdmin)
admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Membership, MembershipAdmin)
admin.site.register(models.Severity, SeverityAdmin)
admin.site.register(models.Priority, PriorityAdmin)
admin.site.register(models.IssueType, IssueTypeAdmin)
admin.site.register(models.ProjectTemplate, ProjectTemplateAdmin)
