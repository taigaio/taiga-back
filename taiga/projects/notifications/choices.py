# -*- coding: utf-8 -*-
import enum
from django.utils.translation import ugettext_lazy as _


class NotifyLevel(enum.IntEnum):
    involved = 1
    all = 2
    none = 3


NOTIFY_LEVEL_CHOICES = (
    (NotifyLevel.involved, _("Involved")),
    (NotifyLevel.all, _("All")),
    (NotifyLevel.none, _("None")),
)


class WebNotificationType(enum.IntEnum):
    assigned = 1
    mentioned = 2
    added_as_watcher = 3
    added_as_member = 4
    comment = 5
    mentioned_in_comment = 6


WEB_NOTIFICATION_TYPE_CHOICES = (
    (WebNotificationType.assigned, _("Assigned")),
    (WebNotificationType.mentioned, _("Mentioned")),
    (WebNotificationType.added_as_watcher, _("Added as watcher")),
    (WebNotificationType.added_as_member, _("Added as member")),
    (WebNotificationType.comment, _("Comment")),
    (WebNotificationType.mentioned_in_comment, _("Mentioned in comment")),
)
