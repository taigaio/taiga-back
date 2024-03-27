# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _


class TaggedMixin(models.Model):
    tags = ArrayField(models.TextField(),
                      null=True, blank=True, default=list, verbose_name=_("tags"))

    class Meta:
        abstract = True


class TagsColorsMixin(models.Model):
    tags_colors = ArrayField(ArrayField(models.TextField(null=True, blank=True), size=2),
                             null=True, blank=True, default=list, verbose_name=_("tags colors"))

    class Meta:
        abstract = True
