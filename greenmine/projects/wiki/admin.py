# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.projects.wiki.models import WikiPage


class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["slug", "project", "owner"]

admin.site.register(WikiPage, WikiPageAdmin)
