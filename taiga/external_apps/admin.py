# -*- coding: utf-8 -*-
from django.contrib import admin

from . import models


class ApplicationAdmin(admin.ModelAdmin):
    readonly_fields=("id",)

admin.site.register(models.Application, ApplicationAdmin)


class ApplicationTokenAdmin(admin.ModelAdmin):
    readonly_fields=("token",)
    search_fields = ("user__username", "user__full_name", "user__email", "application__name")

admin.site.register(models.ApplicationToken, ApplicationTokenAdmin)
