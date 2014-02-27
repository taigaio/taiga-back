# -*- coding: utf-8 -*-

from taiga.base import routers
from taiga.base.auth.api import AuthViewSet
from taiga.base.users.api import UsersViewSet, PermissionsViewSet
from taiga.base.searches.api import SearchViewSet
from taiga.base.domains.api import DomainViewSet, DomainMembersViewSet
from taiga.base.resolver.api import ResolverViewSet
from taiga.projects.api import (ProjectViewSet, MembershipViewSet, InvitationViewSet,
                                    UserStoryStatusViewSet, PointsViewSet, TaskStatusViewSet,
                                    IssueStatusViewSet, IssueTypeViewSet, PriorityViewSet,
                                    SeverityViewSet, ProjectAdminViewSet, RolesViewSet) #, QuestionStatusViewSet)
from taiga.projects.milestones.api import MilestoneViewSet
from taiga.projects.userstories.api import UserStoryViewSet, UserStoryAttachmentViewSet
from taiga.projects.tasks.api import  TaskViewSet, TaskAttachmentViewSet
from taiga.projects.issues.api import IssueViewSet, IssueAttachmentViewSet
#from taiga.projects.questions.api import QuestionViewSet, QuestionAttachmentViewSet
#from taiga.projects.documents.api import DocumentViewSet, DocumentAttachmentViewSet
from taiga.projects.wiki.api import WikiViewSet, WikiAttachmentViewSet


router = routers.DefaultRouter(trailing_slash=False)

# taiga.base.users
router.register(r"users", UsersViewSet, base_name="users")
router.register(r"permissions", PermissionsViewSet, base_name="permissions")
router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"auth", AuthViewSet, base_name="auth")

# taiga.base.resolver
router.register(r"resolver", ResolverViewSet, base_name="resolver")

# taiga.base.searches
router.register(r"search", SearchViewSet, base_name="search")

# taiga.base.domains
router.register(r"sites", DomainViewSet, base_name="sites")
router.register(r"site-members", DomainMembersViewSet, base_name="site-members")
router.register(r"site-projects", ProjectAdminViewSet, base_name="site-projects")

# taiga.projects
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
#router.register(r"question-statuses", QuestionStatusViewSet, base_name="question-statuses")


# taiga.projects.milestones
router.register(r"milestones", MilestoneViewSet, base_name="milestones")

# taiga.projects.userstories
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"userstory-attachments", UserStoryAttachmentViewSet,
                base_name="userstory-attachments")

# taiga.projects.tasks
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"task-attachments", TaskAttachmentViewSet, base_name="task-attachments")

# taiga.projects.issues
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"issue-attachments", IssueAttachmentViewSet, base_name="issue-attachments")

#taiga.projects.questions
# TODO
#router.register(r"questions", QuestionViewSet, base_name="questions")
#router.register(r"question-attachments", QuestionAttachmentViewSet,
#                base_name="question-attachments")

#taiga.projects.documents
# TODO
#router.register(r"documents", DocumentViewSet, base_name="documents")
#router.register(r"document-attachments", DocumentAttachmentViewSet,
#                base_name="document-attachments")

# taiga.projects.wiki
router.register(r"wiki", WikiViewSet, base_name="wiki")
router.register(r"wiki-attachments", WikiAttachmentViewSet, base_name="wiki-attachments")

