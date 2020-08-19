# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
from django.urls import reverse
from django.db import transaction
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from taiga.permissions.choices import ANON_PERMISSIONS
from taiga.projects.notifications.admin import NotifyPolicyInline
from taiga.projects.likes.admin import LikeInline
from taiga.users.admin import RoleInline

from . import models


class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'role', 'user']
    list_display_links = list_display
    raw_id_fields = ["project"]

    def has_add_permission(self, request):
        return False

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["user", "invited_by"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__project=self.obj.project)

        elif db_field.name in ["role"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class MembershipInline(admin.TabularInline):
    model = models.Membership
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        # Hack! Hook parent obj just in time to use in formfield_for_foreignkey
        self.parent_obj = obj
        return super(MembershipInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["user", "invited_by"]):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__project=self.parent_obj)

        elif (db_field.name in ["role"]):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                project=self.parent_obj)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug", "is_private",
                    "owner_url", "blocked_code", "is_featured"]
    list_display_links = ["id", "name", "slug"]
    list_filter = ("is_private", "blocked_code", "is_featured")
    list_editable = ["is_featured", "blocked_code"]
    search_fields = ["id", "name", "slug", "owner__username", "owner__email", "owner__full_name"]
    inlines = [RoleInline,
               MembershipInline,
               NotifyPolicyInline,
               LikeInline]

    fieldsets = (
        (None, {
            "fields": ("name",
                       "slug",
                       "is_featured",
                       "description",
                       "tags",
                       "logo",
                       ("created_date", "modified_date"))
        }),
        (_("Privacy"), {
            "fields": (("owner", "blocked_code"),
                       "is_private",
                       ("anon_permissions", "public_permissions"),
                       "transfer_token")
        }),
        (_("Extra info"), {
            "classes": ("collapse",),
            "fields": ("creation_template",
                       ("is_looking_for_people", "looking_for_people_note")),
        }),
        (_("Modules"), {
            "classes": ("collapse",),
            "fields": (("is_backlog_activated", "total_milestones", "total_story_points"),
                       "is_kanban_activated",
                       "is_issues_activated",
                       "is_wiki_activated",
                       ("videoconferences", "videoconferences_extra_data")),
        }),
        (_("Default values"), {
            "classes": ("collapse",),
            "fields": (("default_us_status", "default_points"),
                       "default_task_status",
                       "default_issue_status",
                       ("default_priority", "default_severity", "default_issue_type")),
        }),
        (_("Activity"), {
            "classes": ("collapse",),
            "fields": (("total_activity", "total_activity_last_week",
                        "total_activity_last_month", "total_activity_last_year"),),
        }),
        (_("Fans"), {
            "classes": ("collapse",),
            "fields": (("total_fans", "total_fans_last_week",
                        "total_fans_last_month", "total_fans_last_year"),),
        }),
    )

    def owner_url(self, obj):
        if obj.owner:
            url = reverse('admin:{0}_{1}_change'.format(obj.owner._meta.app_label,
                                                        obj.owner._meta.model_name),
                          args=(obj.owner.pk,))
            return format_html("<a href='{url}' title='{user}'>{user}</a>", url=url, user=obj.owner)
        return ""
    owner_url.short_description = _('owner')

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["default_points", "default_us_status", "default_task_status",
                              "default_priority", "default_severity",
                              "default_issue_status", "default_issue_type"]):
            if getattr(self, 'obj', None):
                kwargs["queryset"] = db_field.related_model.objects.filter(
                    project=self.obj)
            else:
                kwargs["queryset"] = db_field.related_model.objects.none()

        elif (db_field.name in ["owner"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                memberships__project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def delete_model(self, request, obj):
        obj.delete_related_content()
        super().delete_model(request, obj)

    ## Actions
    actions = [
        "make_public",
        "make_private",
    ]

    @transaction.atomic
    def make_public(self, request, queryset):
        total_updates = 0

        for project in queryset.exclude(is_private=False):
            project.is_private = False

            anon_permissions = list(map(lambda perm: perm[0], ANON_PERMISSIONS))
            project.anon_permissions = list(set((project.anon_permissions or []) + anon_permissions))
            project.public_permissions = list(set((project.public_permissions or []) + anon_permissions))

            project.save()
            total_updates += 1

        self.message_user(request, _("{count} successfully made public.").format(count=total_updates))
    make_public.short_description = _("Make public")

    @transaction.atomic
    def make_private(self, request, queryset):
        total_updates = 0

        for project in queryset.exclude(is_private=True):
            project.is_private = True
            project.anon_permissions = []
            project.public_permissions = []

            project.save()
            total_updates += 1

        self.message_user(request, _("{count} successfully made private.").format(count=total_updates))
    make_private.short_description = _("Make private")

    def delete_queryset(self, request, queryset):
        # NOTE: Override delete_queryset so its use the same approach used in
        # taiga.projects.models.Project.delete_related_content.
        #
        # More info https://docs.djangoproject.com/en/2.2/ref/contrib/admin/actions/#admin-actions

        from taiga.events.apps import (connect_events_signals,
                                       disconnect_events_signals)
        from taiga.projects.tasks.apps import (connect_all_tasks_signals,
                                               disconnect_all_tasks_signals)
        from taiga.projects.userstories.apps import (connect_all_userstories_signals,
                                                     disconnect_all_userstories_signals)
        from taiga.projects.issues.apps import (connect_all_issues_signals,
                                                disconnect_all_issues_signals)
        from taiga.projects.apps import (connect_memberships_signals,
                                         disconnect_memberships_signals)

        disconnect_events_signals()
        disconnect_all_issues_signals()
        disconnect_all_tasks_signals()
        disconnect_all_userstories_signals()
        disconnect_memberships_signals()

        try:
            super().delete_queryset(request, queryset)
        finally:
            connect_events_signals()
            connect_all_issues_signals()
            connect_all_tasks_signals()
            connect_all_userstories_signals()
            connect_memberships_signals()

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
