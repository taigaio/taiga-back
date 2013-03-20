# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.documents.models import Document


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "owner"]

admin.site.register(Document, DocumentAdmin)
