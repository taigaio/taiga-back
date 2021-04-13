# -*- coding: utf-8 -*-
import enum
from django.utils.translation import ugettext_lazy as _


class Section(enum.IntEnum):
    timeline = 1
    epics = 2
    backlog = 3
    kanban = 4
    issues = 5
    wiki = 6


HOMEPAGE_CHOICES = (
    (Section.timeline, _("Timeline")),
    (Section.epics, _("Epics")),
    (Section.backlog, _("Backlog")),
    (Section.kanban, _("Kanban")),
    (Section.issues, _("Issues")),
    (Section.wiki, _("TeamWiki")),
)
