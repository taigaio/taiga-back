# -*- coding: utf-8 -*-
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
