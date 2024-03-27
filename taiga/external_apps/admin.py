# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin

from . import models


class ApplicationAdmin(admin.ModelAdmin):
    readonly_fields=("id",)

admin.site.register(models.Application, ApplicationAdmin)


class ApplicationTokenAdmin(admin.ModelAdmin):
    readonly_fields=("token",)
    search_fields = ("user__username", "user__full_name", "user__email", "application__name")

admin.site.register(models.ApplicationToken, ApplicationTokenAdmin)
