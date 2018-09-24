# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

import enum
from django.utils.translation import ugettext_lazy as _


class Section(enum.IntEnum):
    timeline = 1
    search = 2
    epics = 3
    backlog = 4
    kanban = 5
    issues = 6
    wiki = 7
    team = 8
    admin = 9


HOMEPAGE_CHOICES = (
    (Section.timeline, _("Timeline")),
    (Section.search, _("Search")),
    (Section.epics, _("Epics")),
    (Section.backlog, _("Backlog")),
    (Section.kanban, _("Kanban")),
    (Section.issues, _("Issues")),
    (Section.wiki, _("TeamWiki")),
    (Section.team, _("Team")),
    (Section.admin, _("Admin")),
)
