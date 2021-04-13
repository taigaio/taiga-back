# -*- coding: utf-8 -*-
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
