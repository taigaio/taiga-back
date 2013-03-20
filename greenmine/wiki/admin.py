# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.wiki.models import WikiPage, WikiPageHistory, WikiPageAttachment


class WikiPageAdmin(admin.ModelAdmin):
    list_display = ["slug", "project", "owner"]

admin.site.register(WikiPage, WikiPageAdmin)


class WikiPageHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "wikipage", "owner", "created_date"]

admin.site.register(WikiPageHistory, WikiPageHistoryAdmin)


class WikiPageAttachmentAdmin(admin.ModelAdmin):
    list_display = ["id", "wikipage", "owner"]

admin.site.register(WikiPageAttachment, WikiPageAttachmentAdmin)
