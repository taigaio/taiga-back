# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from taiga.base.api import serializers
from taiga.base.fields import Field, MethodField
from taiga.base.neighbors import NeighborsSerializerMixin

from taiga.mdrender.service import render as mdrender
from taiga.projects.attachments.serializers import BasicAttachmentsInfoSerializerMixin
from taiga.projects.due_dates.serializers import DueDateSerializerMixin
from taiga.projects.mixins.serializers import OwnerExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import ProjectExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import AssignedToExtraInfoSerializerMixin
from taiga.projects.mixins.serializers import StatusExtraInfoSerializerMixin
from taiga.projects.notifications.mixins import WatchedResourceSerializer
from taiga.projects.tagging.serializers import TaggedInProjectResourceSerializer
from taiga.projects.votes.mixins.serializers import VoteResourceSerializerMixin


class IssueListSerializer(VoteResourceSerializerMixin, WatchedResourceSerializer,
                          OwnerExtraInfoSerializerMixin, AssignedToExtraInfoSerializerMixin,
                          StatusExtraInfoSerializerMixin, ProjectExtraInfoSerializerMixin,
                          BasicAttachmentsInfoSerializerMixin, DueDateSerializerMixin,
                          TaggedInProjectResourceSerializer, serializers.LightSerializer):
    id = Field()
    ref = Field()
    severity = Field(attr="severity_id")
    priority = Field(attr="priority_id")
    type = Field(attr="type_id")
    milestone = Field(attr="milestone_id")
    project = Field(attr="project_id")
    created_date = Field()
    modified_date = Field()
    finished_date = Field()
    subject = Field()
    external_reference = Field()
    version = Field()
    watchers = Field()
    is_blocked = Field()
    blocked_note = Field()
    is_closed = Field()


class IssueSerializer(IssueListSerializer):
    comment = MethodField()
    generated_user_stories = MethodField()
    blocked_note_html = MethodField()
    description = Field()
    description_html = MethodField()

    def get_comment(self, obj):
        # NOTE: This method and field is necessary to historical comments work
        return ""

    def get_generated_user_stories(self, obj):
        assert hasattr(obj, "generated_user_stories_attr"),\
            "instance must have a generated_user_stories_attr attribute"
        return obj.generated_user_stories_attr

    def get_blocked_note_html(self, obj):
        return mdrender(obj.project, obj.blocked_note)

    def get_description_html(self, obj):
        return mdrender(obj.project, obj.description)


class IssueNeighborsSerializer(NeighborsSerializerMixin, IssueSerializer):
    pass
