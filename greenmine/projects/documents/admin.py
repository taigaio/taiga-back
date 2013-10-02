# -*- coding: utf-8 -*-

from django.contrib import admin

from . import models


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "owner"]

admin.site.register(models.Document, DocumentAdmin)
