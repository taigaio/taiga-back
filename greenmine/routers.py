# -*- coding: utf-8 -*-

from greenmine.base import routers
from greenmine.base.auth.api import AuthViewSet
from greenmine.base.users.api import RolesViewSet, UsersViewSet
from greenmine.base.searches.api import SearchViewSet
from greenmine.projects.api import ProjectViewSet, MembershipViewSet, InvitationViewSet
from greenmine.projects.milestones.api import MilestoneViewSet
from greenmine.projects.userstories.api import UserStoryViewSet, UserStoryAttachmentViewSet
from greenmine.projects.tasks.api import  TaskViewSet, TaskAttachmentViewSet
from greenmine.projects.issues.api import IssueViewSet, IssueAttachmentViewSet
#from greenmine.projects.questions.api import QuestionViewSet, QuestionAttachmentViewSet
#from greenmine.projects.documents.api import DocumentViewSet, DocumentAttachmentViewSet
from greenmine.projects.wiki.api import WikiViewSet, WikiAttachmentViewSet


router = routers.DefaultRouter(trailing_slash=False)

# greenmine.base.users
router.register(r"users", UsersViewSet, base_name="users")
router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"auth", AuthViewSet, base_name="auth")

# greenmine.base.searches
router.register(r"search", SearchViewSet, base_name="search")

# greenmine.projects
router.register(r"projects", ProjectViewSet, base_name="projects")
router.register(r"memberships", MembershipViewSet, base_name="memberships")
router.register(r"invitations", InvitationViewSet, base_name="invitations")

# greenmine.projects.milestones
router.register(r"milestones", MilestoneViewSet, base_name="milestones")

# greenmine.projects.userstories
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"userstory-attachments", UserStoryAttachmentViewSet,
                base_name="userstory-attachments")

# greenmine.projects.tasks
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"task-attachments", TaskAttachmentViewSet, base_name="task-attachments")

# greenmine.projects.issues
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"issue-attachments", IssueAttachmentViewSet, base_name="issue-attachments")

#greenmine.projects.questions
# TODO
#router.register(r"questions", QuestionViewSet, base_name="questions")
#router.register(r"question-attachments", QuestionAttachmentViewSet,
#                base_name="question-attachments")

#greenmine.projects.documents
# TODO
#router.register(r"documents", DocumentViewSet, base_name="documents")
#router.register(r"document-attachments", DocumentAttachmentViewSet,
#                base_name="document-attachments")

# greenmine.projects.wiki
router.register(r"wiki", WikiViewSet, base_name="wiki")
router.register(r"wiki-attachments", WikiAttachmentViewSet, base_name="wiki-attachments")

