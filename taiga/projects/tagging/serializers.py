# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import MethodField


class TaggedInProjectResourceSerializer(serializers.LightSerializer):
    tags = MethodField()

    def get_tags(self, obj):
        if not obj.tags:
            return []

        project_tag_colors = dict(obj.project.tags_colors)
        return [[tag, project_tag_colors.get(tag, None)] for tag in obj.tags]
