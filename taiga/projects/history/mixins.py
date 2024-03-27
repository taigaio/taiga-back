# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import warnings

from .services import take_snapshot
from taiga.projects.notifications import services as notifications_services
from taiga.base.api import serializers
from taiga.base.fields import MethodField


class HistoryResourceMixin(object):
    """
    Rest Framework resource mixin for resources
    susceptible to have models with history.
    """

    # This attribute will store the last history entry
    # created for this resource. It is mainly used for
    # notifications mixin.
    __last_history = None
    __object_saved = False

    def get_last_history(self):
        if not self.__object_saved:
            message = ("get_last_history() function called before any object are saved. "
                       "Seems you have a wrong mixing order on your resource.")
            warnings.warn(message, RuntimeWarning)
        return self.__last_history

    def get_object_for_snapshot(self, obj):
        """
        Method that returns a model instance ready to snapshot.
        It is by default noop, but should be overwrited when
        snapshot ready instance is found in one of foreign key
        fields.
        """
        return obj

    def persist_history_snapshot(self, obj=None, delete:bool=False):
        """
        Shortcut for resources with special save/persist
        logic.
        """

        user = self.request.user
        comment = ""
        if isinstance(self.request.DATA, dict):
            comment = self.request.DATA.get("comment", "")

        if obj is None:
            obj = self.get_object()

        sobj = self.get_object_for_snapshot(obj)
        if sobj != obj:
            delete = False

        notifications_services.analize_object_for_watchers(obj, comment, user)

        self.__last_history = take_snapshot(sobj, comment=comment, user=user, delete=delete)
        self.__object_saved = True

    def post_save(self, obj, created=False):
        self.persist_history_snapshot(obj=obj)
        super().post_save(obj, created=created)

    def pre_delete(self, obj):
        self.persist_history_snapshot(obj, delete=True)
        super().pre_delete(obj)


class TotalCommentsSerializerMixin(serializers.LightSerializer):
    total_comments = MethodField()

    def get_total_comments(self, obj):
        # The "total_comments" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_comments", 0) or 0
