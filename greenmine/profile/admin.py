# -*- coding: utf-8 -*-
from django.contrib import admin

from greenmine.profile.models import Profile, Role


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user"]

admin.site.register(Profile, ProfileAdmin)


class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]

admin.site.register(Role, RoleAdmin)
