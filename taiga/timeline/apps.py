# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import signals


class TimelineAppConfig(AppConfig):
    name = "taiga.timeline"
    verbose_name = "Timeline"

    def ready(self):
        from . import signals as handlers

        signals.post_save.connect(handlers.on_new_history_entry,
                                  sender=apps.get_model("history", "HistoryEntry"),
                                  dispatch_uid="timeline")
        signals.post_save.connect(handlers.create_membership_push_to_timeline,
                                  sender=apps.get_model("projects", "Membership"))
        signals.pre_delete.connect(handlers.delete_membership_push_to_timeline,
                                   sender=apps.get_model("projects", "Membership"))
        signals.post_save.connect(handlers.create_user_push_to_timeline,
                                  sender=get_user_model())
