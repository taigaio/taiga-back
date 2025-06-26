# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
from django.apps import AppConfig
from django.apps import apps
from django.db.models import signals


def connect_userstories_signals():
    from taiga.projects.tagging import signals as tagging_handlers
    from . import signals as handlers

    # When deleting user stories we must disable task signals while deleting and
    # enabling them in the end
    signals.pre_delete.connect(handlers.disable_task_signals,
                               sender=apps.get_model("userstories", "UserStory"),
                               dispatch_uid='disable_task_signals')

    signals.post_delete.connect(handlers.enable_tasks_signals,
                                sender=apps.get_model("userstories", "UserStory"),
                                dispatch_uid='enable_tasks_signals')

    # Cached prev object version
    signals.pre_save.connect(handlers.cached_prev_us,
                             sender=apps.get_model("userstories", "UserStory"),
                             dispatch_uid="cached_prev_us")

    # Tasks
    signals.post_save.connect(handlers.update_milestone_of_tasks_when_edit_us,
                              sender=apps.get_model("userstories", "UserStory"),
                              dispatch_uid="update_milestone_of_tasks_when_edit_us")

    # Open/Close US and Milestone
    signals.post_save.connect(handlers.try_to_close_or_open_us_and_milestone_when_create_or_edit_us,
                              sender=apps.get_model("userstories", "UserStory"),
                              dispatch_uid="try_to_close_or_open_us_and_milestone_when_create_or_edit_us")
    signals.post_delete.connect(handlers.try_to_close_milestone_when_delete_us,
                                sender=apps.get_model("userstories", "UserStory"),
                                dispatch_uid="try_to_close_milestone_when_delete_us")

    # Tags
    signals.pre_save.connect(tagging_handlers.tags_normalization,
                             sender=apps.get_model("userstories", "UserStory"),
                             dispatch_uid="tags_normalization_user_story")

    # Notify admins on userstory feedback create/update
    signals.post_save.connect(handlers.notify_admins_on_feedback_save,
                              sender=apps.get_model("userstories", "UserStoryFeedback"),
                              dispatch_uid="notify_admins_on_feedback_save")


def connect_userstories_custom_attributes_signals():
    from taiga.projects.custom_attributes import signals as custom_attributes_handlers
    signals.post_save.connect(custom_attributes_handlers.create_custom_attribute_value_when_create_user_story,
                              sender=apps.get_model("userstories", "UserStory"),
                              dispatch_uid="create_custom_attribute_value_when_create_user_story")


def connect_all_userstories_signals():
    connect_userstories_signals()
    connect_userstories_custom_attributes_signals()


def disconnect_userstories_signals():
    signals.pre_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                dispatch_uid="cached_prev_us")

    signals.post_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                 dispatch_uid="update_role_points_when_create_or_edit_us")

    signals.post_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                 dispatch_uid="update_milestone_of_tasks_when_edit_us")

    signals.post_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                 dispatch_uid="try_to_close_or_open_us_and_milestone_when_create_or_edit_us")
    signals.post_delete.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                   dispatch_uid="try_to_close_milestone_when_delete_us")

    signals.pre_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                dispatch_uid="tags_normalization_user_story")


def disconnect_userstories_custom_attributes_signals():
    signals.post_save.disconnect(sender=apps.get_model("userstories", "UserStory"),
                                 dispatch_uid="create_custom_attribute_value_when_create_user_story")


def disconnect_all_userstories_signals():
    disconnect_userstories_signals()
    disconnect_userstories_custom_attributes_signals()


class UserStoriesAppConfig(AppConfig):
    name = "taiga.projects.userstories"
    verbose_name = "User Stories"
    watched_types = ["userstories.userstory", ]

    def ready(self):
        connect_all_userstories_signals()
