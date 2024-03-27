# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import validators
from taiga.base.api import serializers
from taiga.projects.notifications.validators import WatchersValidator

from . import models


class WikiPageValidator(WatchersValidator, validators.ModelValidator):
    slug = serializers.CharField()

    class Meta:
        model = models.WikiPage
        read_only_fields = ('modified_date', 'created_date', 'owner')


class WikiLinkValidator(validators.ModelValidator):
    class Meta:
        model = models.WikiLink
        read_only_fields = ('href',)
