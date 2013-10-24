# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.projects.wiki.models import WikiPage
from greenmine.projects.admin import AttachmentInline

from . import models

class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["project", "slug", "owner"]
    list_display_links = list_display
    inlines = [AttachmentInline]

admin.site.register(models.WikiPage, WikiPageAdmin)
