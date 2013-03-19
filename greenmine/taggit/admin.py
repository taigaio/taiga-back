# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib import admin

from .models import Tag, TaggedItem


class TaggedItemInline(admin.StackedInline):
    model = TaggedItem

class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = [
        TaggedItemInline
    ]


admin.site.register(Tag, TagAdmin)
