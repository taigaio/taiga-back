# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin

from . import models


class ContactEntryAdmin(admin.ModelAdmin):
    list_display = ["created_date", "project", "user"]
    list_display_links = list_display
    list_filter = ["created_date", ]
    date_hierarchy = "created_date"
    ordering = ("-created_date", "id")
    search_fields = ("project__name", "project__slug", "user__username", "user__email", "user__full_name")

admin.site.register(models.ContactEntry, ContactEntryAdmin)
