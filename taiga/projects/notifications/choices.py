import enum
from django.utils.translation import ugettext_lazy as _


class NotifyLevel(enum.IntEnum):
    notwatch = 1
    watch = 2
    ignore = 3


NOTIFY_LEVEL_CHOICES = (
    (NotifyLevel.notwatch, _("Not watching")),
    (NotifyLevel.watch, _("Watching")),
    (NotifyLevel.ignore, _("Ignoring")),
)


