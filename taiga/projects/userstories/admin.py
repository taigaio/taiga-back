# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin

from taiga.projects.attachments.admin import AttachmentInline
from taiga.projects.notifications.admin import WatchedInline
from taiga.projects.votes.admin import VoteInline

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
    readonly_fields = ["user_story", "role", "points"]


class UserStoryAdmin(admin.ModelAdmin):
    list_display = ["project", "milestone",  "ref", "subject",]
    list_display_links = ["ref", "subject",]
    inlines = [RolePointsInline, WatchedInline, VoteInline]
    raw_id_fields = ["project"]
    search_fields = ["subject", "description", "id", "ref"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["status", "milestone", "generated_from_issue",
                              "generated_from_task"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                                      project=self.obj.project)
        elif (db_field.name in ["owner", "assigned_to"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(
                                         memberships__project=self.obj.project)
        elif (db_field.name in ["assigned_users"]
                and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(models.UserStory, UserStoryAdmin)
admin.site.register(models.RolePoints, RolePointsAdmin)
