# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from . import models


class LikeInline(GenericTabularInline):
    model = models.Like
    extra = 0
    raw_id_fields = ["user"]
