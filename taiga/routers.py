# -*- coding: utf-8 -*-

from taiga.base import routers

router = routers.DefaultRouter(trailing_slash=False)


# Users & Auth
from taiga.base.users.api import UsersViewSet
from taiga.base.users.api import PermissionsViewSet
from taiga.base.auth.api import AuthViewSet

router.register(r"users", UsersViewSet, base_name="users")
router.register(r"permissions", PermissionsViewSet, base_name="permissions")
router.register(r"auth", AuthViewSet, base_name="auth")


# Resolver & Search
from taiga.base.resolver.api import ResolverViewSet
from taiga.base.searches.api import SearchViewSet

router.register(r"resolver", ResolverViewSet, base_name="resolver")
router.register(r"search", SearchViewSet, base_name="search")


# Domains
from taiga.domains.api import DomainViewSet
from taiga.domains.api import DomainMembersViewSet
from taiga.projects.api import ProjectAdminViewSet

router.register(r"sites", DomainViewSet, base_name="sites")
router.register(r"site-members", DomainMembersViewSet, base_name="site-members")
router.register(r"site-projects", ProjectAdminViewSet, base_name="site-projects")


# Projects & Types
from taiga.projects.api import RolesViewSet
from taiga.projects.api import ProjectViewSet
from taiga.projects.api import MembershipViewSet
from taiga.projects.api import InvitationViewSet
from taiga.projects.api import UserStoryStatusViewSet
from taiga.projects.api import PointsViewSet
from taiga.projects.api import TaskStatusViewSet
from taiga.projects.api import IssueStatusViewSet
from taiga.projects.api import IssueTypeViewSet
from taiga.projects.api import PriorityViewSet
from taiga.projects.api import SeverityViewSet

router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"projects", ProjectViewSet, base_name="projects")
router.register(r"memberships", MembershipViewSet, base_name="memberships")
router.register(r"invitations", InvitationViewSet, base_name="invitations")
router.register(r"userstory-statuses", UserStoryStatusViewSet, base_name="userstory-statuses")
router.register(r"points", PointsViewSet, base_name="points")
router.register(r"task-statuses", TaskStatusViewSet, base_name="task-statuses")
router.register(r"issue-statuses", IssueStatusViewSet, base_name="issue-statuses")
router.register(r"issue-types", IssueTypeViewSet, base_name="issue-types")
router.register(r"priorities", PriorityViewSet, base_name="priorities")
router.register(r"severities",SeverityViewSet , base_name="severities")


# Project components
from taiga.projects.milestones.api import MilestoneViewSet
from taiga.projects.userstories.api import UserStoryViewSet
from taiga.projects.userstories.api import UserStoryAttachmentViewSet
from taiga.projects.tasks.api import TaskViewSet
from taiga.projects.tasks.api import TaskAttachmentViewSet
from taiga.projects.issues.api import IssueViewSet
from taiga.projects.issues.api import IssueAttachmentViewSet
from taiga.projects.wiki.api import WikiViewSet
from taiga.projects.wiki.api import WikiAttachmentViewSet

router.register(r"milestones", MilestoneViewSet, base_name="milestones")
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"userstory-attachments", UserStoryAttachmentViewSet, base_name="userstory-attachments")
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"task-attachments", TaskAttachmentViewSet, base_name="task-attachments")
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"issue-attachments", IssueAttachmentViewSet, base_name="issue-attachments")
router.register(r"wiki", WikiViewSet, base_name="wiki")
router.register(r"wiki-attachments", WikiAttachmentViewSet, base_name="wiki-attachments")
