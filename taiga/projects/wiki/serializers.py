# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.projects.history import services as history_service
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.mdrender.service import render as mdrender


class WikiPageSerializer(
    WatchedResourceSerializer, ProjectExtraInfoSerializerMixin,
    serializers.LightSerializer
):
    id = Field()
    project = Field(attr="project_id")
    slug = Field()
    content = Field()
    owner = Field(attr="owner_id")
    last_modifier = Field(attr="last_modifier_id")
    created_date = Field()
    modified_date = Field()

    html = MethodField()
    editions = MethodField()

    version = Field()

    def get_html(self, obj):
        return mdrender(obj.project, obj.content)

    def get_editions(self, obj):
        return history_service.get_history_queryset_by_model_instance(obj).count() + 1  # +1 for creation


class WikiLinkSerializer(serializers.LightSerializer):
    id = Field()
    project = Field(attr="project_id")
    title = Field()
    href = Field()
    order = Field()
