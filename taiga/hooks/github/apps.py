# -*- coding: utf-8 -*-
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
