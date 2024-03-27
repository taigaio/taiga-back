# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin

from . import models


class FeedbackEntryAdmin(admin.ModelAdmin):
    list_display = ['created_date', 'full_name', 'email' ]
    list_display_links = list_display
    list_filter = ['created_date',]
    date_hierarchy = "created_date"
    ordering = ("-created_date", "id")
    search_fields = ("full_name", "email", "id")


admin.site.register(models.FeedbackEntry, FeedbackEntryAdmin)
