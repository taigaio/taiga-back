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

from taiga.projects.wiki.models import WikiPage

from . import models

class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["project", "slug", "owner"]
    list_display_links = list_display
    inlines = [WatchedInline, VoteInline]
    raw_id_fields = ["project"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name in ["owner", "last_modifier"] and getattr(self, 'obj', None)):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(models.WikiPage, WikiPageAdmin)

class WikiLinkAdmin(admin.ModelAdmin):
    list_display = ["project", "title"]
    list_display_links = list_display
    raw_id_fields = ["project"]

admin.site.register(models.WikiLink, WikiLinkAdmin)
