# -*- coding: utf-8 -*-

from django.contrib import admin

from greenmine.wiki.models import WikiPage, WikiPageAttachment


class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["slug", "project", "owner"]

admin.site.register(WikiPage, WikiPageAdmin)


class WikiPageAttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "wikipage", "owner"]

admin.site.register(WikiPageAttachment, WikiPageAttachmentAdmin)
