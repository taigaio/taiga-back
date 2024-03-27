# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.admin import TabularInline

from . import models


class WatchedInline(GenericTabularInline):
    model = models.Watched
    extra = 0
    raw_id_fields = ["project", "user"]


class NotifyPolicyInline(TabularInline):
    model = models.NotifyPolicy
    extra = 0
    readonly_fields = ("notify_level", "live_notify_level")
    raw_id_fields = ["user"]
