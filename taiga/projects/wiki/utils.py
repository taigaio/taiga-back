# -*- coding: utf-8 -*-
from taiga.projects.notifications.utils import attach_watchers_to_queryset
from taiga.projects.notifications.utils import attach_total_watchers_to_queryset
from taiga.projects.notifications.utils import attach_is_watcher_to_queryset


def attach_extra_info(queryset, user=None, include_attachments=False):
    queryset = attach_watchers_to_queryset(queryset)
    queryset = attach_total_watchers_to_queryset(queryset)
    queryset = attach_is_watcher_to_queryset(queryset, user)
    return queryset
