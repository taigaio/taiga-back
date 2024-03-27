# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin

from taiga.projects.notifications.admin import WatchedInline
from taiga.projects.votes.admin import VoteInline

from . import models


class RelatedUserStoriesInline(admin.TabularInline):
    model = models.RelatedUserStory
    sortable_field_name = "order"
    raw_id_fields = ["user_story", ]
    extra = 0


class EpicAdmin(admin.ModelAdmin):
    list_display = ["project", "ref", "subject"]
    list_display_links = ["ref", "subject"]
    inlines = [WatchedInline, VoteInline, RelatedUserStoriesInline]
    raw_id_fields = ["project"]
    search_fields = ["subject", "description", "id", "ref"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["status"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(project=self.obj.project)

        elif (db_field.name in ["owner", "assigned_to"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(memberships__project=self.obj.project)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name in ["watchers"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related.parent_model.objects.filter(memberships__project=self.obj.project)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(models.Epic, EpicAdmin)
