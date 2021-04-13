# -*- coding: utf-8 -*-
from django.contrib import admin

from . import models


class BaseCustomAttributeAdmin:
    list_display = ["id", "name", "type", "project", "order"]
    list_display_links = ["id", "name"]
    fieldsets = (
        (None, {
            "fields": ("name", "type", "description", ("project", "order"))
        }),
        ("Advanced options", {
            "classes": ("collapse",),
            "fields": (("created_date", "modified_date"),)
        })
    )
    readonly_fields = ("created_date", "modified_date")
    search_fields = ["id", "name", "project__name", "project__slug"]
    raw_id_fields = ["project"]


@admin.register(models.EpicCustomAttribute)
class EpicCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass


@admin.register(models.UserStoryCustomAttribute)
class UserStoryCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass


@admin.register(models.TaskCustomAttribute)
class TaskCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass


@admin.register(models.IssueCustomAttribute)
class IssueCustomAttributeAdmin(BaseCustomAttributeAdmin, admin.ModelAdmin):
    pass
