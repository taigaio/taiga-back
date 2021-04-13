# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


class LikeInline(GenericTabularInline):
    model = models.Like
    extra = 0
    raw_id_fields = ["user"]
