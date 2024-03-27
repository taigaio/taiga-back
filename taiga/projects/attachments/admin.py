# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "project", "attached_file", "owner", "content_type", "content_object"]
    list_display_links = ["id", "attached_file",]
    search_fields = ["id", "attached_file", "project__name", "project__slug"]
    raw_id_fields = ["project"]

    def get_object(self, *args, **kwargs):
        self.obj = super().get_object(*args, **kwargs)
        return self.obj

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ["owner"] and getattr(self, 'obj', None):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                                         memberships__project=self.obj.project)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AttachmentInline(GenericTabularInline):
     model = models.Attachment
     fields = ("attached_file", "owner")
     extra = 0


admin.site.register(models.Attachment, AttachmentAdmin)
