# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from django.apps import AppConfig
from django.apps import apps

from taiga.hooks.github.signals import handle_move_on_destroy_issue_status


def _connect_all_signals():
    from taiga.projects.signals import issue_status_post_move_on_destroy as issue_status_post_move_on_destroy_signal

    issue_status_post_move_on_destroy_signal.connect(handle_move_on_destroy_issue_status,
                                                     sender=apps.get_model("projects", "IssueStatus"),
                                                     dispatch_uid="move_on_destroy_issue_status_on_github")

def _disconnect_all_signals():
    from taiga.projects.signals import issue_status_post_move_on_destroy as issue_status_post_move_on_destroy_signal

    issue_status_post_move_on_destroy_signal.disconnect(sender=apps.get_model("projects", "IssueStatus"),
                                                        dispatch_uid="move_on_destroy_issue_status_on_github")


class GithubHooksAppConfig(AppConfig):
    name = "taiga.hooks.github"
    verbose_name = "GithubHooks"
    watched_types = []

    def ready(self):
        _connect_all_signals()
