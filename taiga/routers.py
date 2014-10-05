# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
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

from taiga.base import routers

router = routers.DefaultRouter(trailing_slash=False)

# taiga.users
from taiga.users.api import UsersViewSet
from taiga.auth.api import AuthViewSet

router.register(r"users", UsersViewSet, base_name="users")
router.register(r"auth", AuthViewSet, base_name="auth")


#taiga.userstorage
from taiga.userstorage.api import StorageEntriesViewSet

router.register(r"user-storage", StorageEntriesViewSet, base_name="user-storage")


# Resolver
from taiga.projects.references.api import ResolverViewSet

router.register(r"resolver", ResolverViewSet, base_name="resolver")


# Search
from taiga.searches.api import SearchViewSet

router.register(r"search", SearchViewSet, base_name="search")


# Importer
from taiga.export_import.api import ProjectImporterViewSet

router.register(r"importer", ProjectImporterViewSet, base_name="importer")


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
from taiga.projects.api import ProjectTemplateViewSet


router.register(r"roles", RolesViewSet, base_name="roles")
router.register(r"projects", ProjectViewSet, base_name="projects")
router.register(r"project-templates", ProjectTemplateViewSet, base_name="project-templates")
router.register(r"memberships", MembershipViewSet, base_name="memberships")
router.register(r"invitations", InvitationViewSet, base_name="invitations")
router.register(r"userstory-statuses", UserStoryStatusViewSet, base_name="userstory-statuses")
router.register(r"points", PointsViewSet, base_name="points")
router.register(r"task-statuses", TaskStatusViewSet, base_name="task-statuses")
router.register(r"issue-statuses", IssueStatusViewSet, base_name="issue-statuses")
router.register(r"issue-types", IssueTypeViewSet, base_name="issue-types")
router.register(r"priorities", PriorityViewSet, base_name="priorities")
router.register(r"severities",SeverityViewSet , base_name="severities")

# Attachments
from taiga.projects.attachments.api import UserStoryAttachmentViewSet
from taiga.projects.attachments.api import IssueAttachmentViewSet
from taiga.projects.attachments.api import TaskAttachmentViewSet
from taiga.projects.attachments.api import WikiAttachmentViewSet

router.register(r"userstories/attachments", UserStoryAttachmentViewSet, base_name="userstory-attachments")
router.register(r"tasks/attachments", TaskAttachmentViewSet, base_name="task-attachments")
router.register(r"issues/attachments", IssueAttachmentViewSet, base_name="issue-attachments")
router.register(r"wiki/attachments", WikiAttachmentViewSet, base_name="wiki-attachments")


# History & Components
from taiga.projects.history.api import UserStoryHistory
from taiga.projects.history.api import TaskHistory
from taiga.projects.history.api import IssueHistory
from taiga.projects.history.api import WikiHistory

router.register(r"history/userstory", UserStoryHistory, base_name="userstory-history")
router.register(r"history/task", TaskHistory, base_name="task-history")
router.register(r"history/issue", IssueHistory, base_name="issue-history")
router.register(r"history/wiki", WikiHistory, base_name="wiki-history")


# Timelines
from taiga.timeline.api import UserTimeline
from taiga.timeline.api import ProjectTimeline

router.register(r"timeline/user", UserTimeline, base_name="user-timeline")
router.register(r"timeline/project", ProjectTimeline, base_name="project-timeline")


# Project components
from taiga.projects.milestones.api import MilestoneViewSet
from taiga.projects.userstories.api import UserStoryViewSet
from taiga.projects.tasks.api import TaskViewSet
from taiga.projects.issues.api import IssueViewSet
from taiga.projects.issues.api import VotersViewSet
from taiga.projects.wiki.api import WikiViewSet, WikiLinkViewSet

router.register(r"milestones", MilestoneViewSet, base_name="milestones")
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"issues/(?P<issue_id>\d+)/voters", VotersViewSet, base_name="issue-voters")
router.register(r"wiki", WikiViewSet, base_name="wiki")
router.register(r"wiki-links", WikiLinkViewSet, base_name="wiki-links")

# Notify policies
from taiga.projects.notifications.api import NotifyPolicyViewSet

router.register(r"notify-policies", NotifyPolicyViewSet, base_name="notifications")


# feedback
#   - see taiga.feedback.routers and taiga.feedback.apps


