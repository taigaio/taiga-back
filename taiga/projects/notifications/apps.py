# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django import dispatch
from django.apps import AppConfig


signal_assigned_to = dispatch.Signal()  # providing_args=["user", "obj"]
signal_assigned_users = dispatch.Signal()  # providing_args=["user", "obj", "new_assigned_users"]
signal_watchers_added = dispatch.Signal()  # providing_args=["user", "obj", "new_watchers"]
signal_members_added = dispatch.Signal()  # providing_args=["user", "project", "new_members"]
signal_mentions = dispatch.Signal()  # providing_args=["user", "obj", "mentions"]
signal_comment = dispatch.Signal()  # providing_args=["user", "obj", "watchers"]
signal_comment_mentions = dispatch.Signal()  # providing_args=["user", "obj", "mentions"]


class NotificationsAppConfig(AppConfig):
    name = "taiga.projects.notifications"
    verbose_name = "Notifications"

    def ready(self):
        from . import signals as handlers
        signal_assigned_to.connect(handlers.on_assigned_to)
        signal_assigned_users.connect(handlers.on_assigned_users)
        signal_watchers_added.connect(handlers.on_watchers_added)
        signal_members_added.connect(handlers.on_members_added)
        signal_mentions.connect(handlers.on_mentions)
        signal_comment.connect(handlers.on_comment)
        signal_comment_mentions.connect(handlers.on_comment_mentions)
