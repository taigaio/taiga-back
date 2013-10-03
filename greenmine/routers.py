# -*- coding: utf-8 -*-

from greenmine.base import routers
from greenmine.base.api import ApiRoot
from greenmine.base.users.api import AuthViewSet, RolesViewSet, UsersViewSet
from greenmine.base.searches.api import SearchViewSet
from greenmine.projects.api import ProjectViewSet
from greenmine.projects.milestones.api import MilestoneViewSet
from greenmine.projects.userstories.api import (PointsViewSet, UserStoryStatusViewSet,
                                                UserStoryViewSet,)
from greenmine.projects.tasks.api import TaskStatusViewSet, TaskViewSet, TasksAttachmentViewSet
from greenmine.projects.issues.api import (PriorityViewSet, SeverityViewSet,
                                           IssueStatusViewSet, IssueTypeViewSet,
                                           IssueViewSet, IssuesAttachmentViewSet,)


router = routers.DefaultRouter(trailing_slash=False)

# greenmine.base.users
router.register(r"users", UsersViewSet, base_name="users")
router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"auth", AuthViewSet, base_name="auth")

# greenmine.base.searches
router.register(r"search", SearchViewSet, base_name="search")

# greenmine.projects
router.register(r"projects", ProjectViewSet, base_name="projects")

# greenmine.projects.milestones
router.register(r"milestones", MilestoneViewSet, base_name="milestones")

# greenmine.projects.userstories
router.register(r"points", PointsViewSet, base_name="points")
router.register(r"userstory-statuses", UserStoryStatusViewSet, base_name="userstory-statuses")
router.register(r"userstories", UserStoryViewSet, base_name="userstories")

# greenmine.projects.tasks
router.register(r"task-statuses", TaskStatusViewSet, base_name="task-statuses")
router.register(r"task-attachments", TasksAttachmentViewSet, base_name="task-attachments")
router.register(r"tasks", TaskViewSet, base_name="tasks")

# greenmine.projects.issues
router.register(r"severities", SeverityViewSet, base_name="severities")
router.register(r"priorities", PriorityViewSet, base_name="priorities")
router.register(r"issue-statuses", IssueStatusViewSet, base_name="issue-statuses")
router.register(r"issue-types", IssueTypeViewSet, base_name="issue-types")
router.register(r"issue-attachments", IssuesAttachmentViewSet, base_name="issue-attachments")
router.register(r"issues", IssueViewSet, base_name="issues")

#greenmine.projects.questions
# TODO
#greenmine.projects.wiki
# TODO
#greenmine.projects.documents
# TODO
