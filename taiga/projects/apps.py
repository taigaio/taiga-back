# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from django.apps import AppConfig
from django.apps import apps
from django.db.models import signals


## Project Signals

def connect_projects_signals():
    from . import signals as handlers
    from .tagging import signals as tagging_handlers
    # On project object is created apply template.
    signals.post_save.connect(handlers.project_post_save,
                              sender=apps.get_model("projects", "Project"),
                              dispatch_uid='project_post_save')

    # Tags normalization after save a project
    signals.pre_save.connect(tagging_handlers.tags_normalization,
                             sender=apps.get_model("projects", "Project"),
                             dispatch_uid="tags_normalization_projects")


def disconnect_projects_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "Project"),
                                 dispatch_uid='project_post_save')
    signals.pre_save.disconnect(sender=apps.get_model("projects", "Project"),
                                dispatch_uid="tags_normalization_projects")


## Memberships Signals

def connect_memberships_signals():
    from . import signals as handlers
    # On membership object is deleted, update role-points relation.
    signals.pre_delete.connect(handlers.membership_post_delete,
                               sender=apps.get_model("projects", "Membership"),
                               dispatch_uid='membership_pre_delete')

    # On membership object is created, reorder and create notify policies
    signals.post_save.connect(handlers.membership_post_save,
                              sender=apps.get_model("projects", "Membership"),
                              dispatch_uid='membership_post_save')


def disconnect_memberships_signals():
    signals.pre_delete.disconnect(sender=apps.get_model("projects", "Membership"),
                                  dispatch_uid='membership_pre_delete')
    signals.post_save.disconnect(sender=apps.get_model("projects", "Membership"),
                                 dispatch_uid='membership_post_save')


## US Statuses Signals

def connect_us_status_signals():
    from . import signals as handlers
    signals.post_save.connect(handlers.try_to_close_or_open_user_stories_when_edit_us_status,
                              sender=apps.get_model("projects", "UserStoryStatus"),
                              dispatch_uid="try_to_close_or_open_user_stories_when_edit_us_status")
    signals.post_save.connect(handlers.create_swimlane_user_story_statuses_on_userstory_status_post_save,
                              sender=apps.get_model("projects", "UserStoryStatus"),
                              dispatch_uid="create_swimlane_user_story_statuses_on_userstory_status_post_save")


def disconnect_us_status_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "UserStoryStatus"),
                                 dispatch_uid="try_to_close_or_open_user_stories_when_edit_us_status")
    signals.post_save.disconnect(sender=apps.get_model("projects", "UserStoryStatus"),
                                 dispatch_uid="create_swimlane_user_story_statuses_on_userstory_status_post_save")


## Swimlane Signals

def connect_swimlane_signals():
    from . import signals as handlers
    signals.post_save.connect(handlers.create_swimlane_user_story_statuses_on_swimalne_post_save,
                              sender=apps.get_model("projects", "Swimlane"),
                              dispatch_uid="create_swimlane_user_story_statuses_on_swimalne_post_save")
    signals.post_save.connect(handlers.set_default_project_swimlane_on_swimalne_post_save,
                              sender=apps.get_model("projects", "Swimlane"),
                              dispatch_uid="set_default_project_swimlane_on_swimalne_post_save")


def disconnect_swimlane_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "Swimlane"),
                                 dispatch_uid="create_swimlane_user_story_statuses_on_swimalne_post_save")
    signals.post_save.disconnect(sender=apps.get_model("projects", "Swimlane"),
                                 dispatch_uid="set_default_project_swimlane_on_swimalne_post_save")



## Tasks Statuses Signals

def connect_task_status_signals():
    from . import signals as handlers
    signals.post_save.connect(handlers.try_to_close_or_open_user_stories_when_edit_task_status,
                              sender=apps.get_model("projects", "TaskStatus"),
                              dispatch_uid="try_to_close_or_open_user_stories_when_edit_task_status")


def disconnect_task_status_signals():
    signals.post_save.disconnect(sender=apps.get_model("projects", "TaskStatus"),
                                 dispatch_uid="try_to_close_or_open_user_stories_when_edit_task_status")


class ProjectsAppConfig(AppConfig):
    name = "taiga.projects"
    verbose_name = "Projects"
    watched_types = [
      "projects.userstorystatus",
      "projects.swimlane",
      "projects.swimlaneuserstorystatus"
    ]

    def ready(self):
        connect_projects_signals()
        connect_memberships_signals()
        connect_us_status_signals()
        connect_swimlane_signals()
        connect_task_status_signals()
