# -*- coding: utf-8 -*-
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
