# Copyright (C) 2014-2019 Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.apps import AppConfig
from django.apps import apps
from django.db.models import signals


def connect_issues_signals():
    from taiga.projects.tagging import signals as tagging_handlers
    from . import signals as handlers

    # Cached prev object version
    signals.pre_save.connect(handlers.cached_prev_issue,
                             sender=apps.get_model("issues", "Issue"),
                             dispatch_uid="cached_prev_issue")

    # Finished date
    signals.pre_save.connect(handlers.set_finished_date_when_edit_issue,
                             sender=apps.get_model("issues", "Issue"),
                             dispatch_uid="set_finished_date_when_edit_issue")

    # Tags
    signals.pre_save.connect(tagging_handlers.tags_normalization,
                             sender=apps.get_model("issues", "Issue"),
                             dispatch_uid="tags_normalization_issue")

    # Open/Close US and Milestone
    signals.post_save.connect(handlers.try_to_close_or_open_milestone_when_create_or_edit_issue,
                              sender=apps.get_model("issues", "Issue"),
                              dispatch_uid="try_to_close_or_open_milestone_when_create_or_edit_issue")
    signals.post_delete.connect(handlers.try_to_close_milestone_when_delete_issue,
                                sender=apps.get_model("issues", "Issue"),
                                dispatch_uid="try_to_close_milestone_when_delete_issue")


def connect_issues_custom_attributes_signals():
    from taiga.projects.custom_attributes import signals as custom_attributes_handlers

    signals.post_save.connect(custom_attributes_handlers.create_custom_attribute_value_when_create_issue,
                              sender=apps.get_model("issues", "Issue"),
                              dispatch_uid="create_custom_attribute_value_when_create_issue")


def connect_all_issues_signals():
    connect_issues_signals()
    connect_issues_custom_attributes_signals()


def disconnect_issues_signals():
    signals.pre_save.disconnect(sender=apps.get_model("issues", "Issue"),
                                dispatch_uid="cached_prev_issue")

    signals.pre_save.disconnect(sender=apps.get_model("issues", "Issue"),
                                dispatch_uid="set_finished_date_when_edit_issue")
    signals.pre_save.disconnect(sender=apps.get_model("issues", "Issue"),
                                dispatch_uid="tags_normalization_issue")

    signals.post_save.disconnect(sender=apps.get_model("issues", "Issue"),
                                 dispatch_uid="try_to_close_or_open_milestone_when_create_or_edit_issue")
    signals.post_delete.disconnect(sender=apps.get_model("issues", "Issue"),
                                   dispatch_uid="try_to_close_milestone_when_delete_issue")


def disconnect_issues_custom_attributes_signals():
    signals.post_save.disconnect(sender=apps.get_model("issues", "Issue"),
                                 dispatch_uid="create_custom_attribute_value_when_create_issue")


def disconnect_all_issues_signals():
    disconnect_issues_signals()
    disconnect_issues_custom_attributes_signals()


class IssuesAppConfig(AppConfig):
    name = "taiga.projects.issues"
    verbose_name = "Issues"
    watched_types = ["issues.issue", ]

    def ready(self):
        connect_all_issues_signals()
