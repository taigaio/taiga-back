# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from collections import OrderedDict

from .generics import GenericSitemap

from .projects import ProjectsSitemap
from .projects import ProjectBacklogsSitemap
from .projects import ProjectKanbansSitemap

from .epics import EpicsSitemap

from .milestones import MilestonesSitemap

from .userstories import UserStoriesSitemap

from .tasks import TasksSitemap

from .issues import IssuesSitemap

from .wiki import WikiPagesSitemap

from .users import UsersSitemap


sitemaps = OrderedDict([
    ("generics", GenericSitemap),

    ("projects", ProjectsSitemap),
    ("project-backlogs", ProjectBacklogsSitemap),
    ("project-kanbans", ProjectKanbansSitemap),

    ("epics", EpicsSitemap),

    ("milestones", MilestonesSitemap),

    ("userstories", UserStoriesSitemap),

    ("tasks", TasksSitemap),

    ("issues", IssuesSitemap),

    ("wikipages", WikiPagesSitemap),

    ("users", UsersSitemap)
])
