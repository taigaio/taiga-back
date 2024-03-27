# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import enum
from django.utils.translation import gettext_lazy as _


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
