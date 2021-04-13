# -*- coding: utf-8 -*-
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
