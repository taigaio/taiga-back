# -*- coding: utf-8 -*-
# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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

# Locales
from taiga.locale.api import LocalesViewSet

router.register(r"locales", LocalesViewSet, base_name="locales")


# Users & Roles
from taiga.auth.api import AuthViewSet
from taiga.users.api import UsersViewSet
from taiga.users.api import RolesViewSet

router.register(r"auth", AuthViewSet, base_name="auth")
router.register(r"users", UsersViewSet, base_name="users")
router.register(r"roles", RolesViewSet, base_name="roles")


# User Storage
from taiga.userstorage.api import StorageEntriesViewSet

router.register(r"user-storage", StorageEntriesViewSet, base_name="user-storage")


# Notify policies
from taiga.projects.notifications.api import NotifyPolicyViewSet

router.register(r"notify-policies", NotifyPolicyViewSet, base_name="notifications")


# Projects & Selectors
from taiga.projects.api import ProjectViewSet
from taiga.projects.api import ProjectFansViewSet
from taiga.projects.api import ProjectWatchersViewSet
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

router.register(r"projects", ProjectViewSet, base_name="projects")
router.register(r"projects/(?P<resource_id>\d+)/fans", ProjectFansViewSet, base_name="project-fans")
router.register(r"projects/(?P<resource_id>\d+)/watchers", ProjectWatchersViewSet, base_name="project-watchers")
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


# Custom Attributes
from taiga.projects.custom_attributes.api import UserStoryCustomAttributeViewSet
from taiga.projects.custom_attributes.api import TaskCustomAttributeViewSet
from taiga.projects.custom_attributes.api import IssueCustomAttributeViewSet
from taiga.projects.custom_attributes.api import UserStoryCustomAttributesValuesViewSet
from taiga.projects.custom_attributes.api import TaskCustomAttributesValuesViewSet
from taiga.projects.custom_attributes.api import IssueCustomAttributesValuesViewSet

router.register(r"userstory-custom-attributes", UserStoryCustomAttributeViewSet,
                base_name="userstory-custom-attributes")
router.register(r"task-custom-attributes", TaskCustomAttributeViewSet,
                base_name="task-custom-attributes")
router.register(r"issue-custom-attributes", IssueCustomAttributeViewSet,
                base_name="issue-custom-attributes")

router.register(r"userstories/custom-attributes-values", UserStoryCustomAttributesValuesViewSet,
                base_name="userstory-custom-attributes-values")
router.register(r"tasks/custom-attributes-values", TaskCustomAttributesValuesViewSet,
                base_name="task-custom-attributes-values")
router.register(r"issues/custom-attributes-values", IssueCustomAttributesValuesViewSet,
                base_name="issue-custom-attributes-values")


# Search
from taiga.searches.api import SearchViewSet

router.register(r"search", SearchViewSet, base_name="search")


# Resolver
from taiga.projects.references.api import ResolverViewSet

router.register(r"resolver", ResolverViewSet, base_name="resolver")


# Attachments
from taiga.projects.attachments.api import UserStoryAttachmentViewSet
from taiga.projects.attachments.api import IssueAttachmentViewSet
from taiga.projects.attachments.api import TaskAttachmentViewSet
from taiga.projects.attachments.api import WikiAttachmentViewSet

router.register(r"userstories/attachments", UserStoryAttachmentViewSet,
                base_name="userstory-attachments")
router.register(r"tasks/attachments", TaskAttachmentViewSet, base_name="task-attachments")
router.register(r"issues/attachments", IssueAttachmentViewSet, base_name="issue-attachments")
router.register(r"wiki/attachments", WikiAttachmentViewSet, base_name="wiki-attachments")


# Project components
from taiga.projects.milestones.api import MilestoneViewSet
from taiga.projects.milestones.api import MilestoneWatchersViewSet
from taiga.projects.userstories.api import UserStoryViewSet
from taiga.projects.userstories.api import UserStoryVotersViewSet
from taiga.projects.userstories.api import UserStoryWatchersViewSet
from taiga.projects.tasks.api import TaskViewSet
from taiga.projects.tasks.api import TaskVotersViewSet
from taiga.projects.tasks.api import TaskWatchersViewSet
from taiga.projects.issues.api import IssueViewSet
from taiga.projects.issues.api import IssueVotersViewSet
from taiga.projects.issues.api import IssueWatchersViewSet
from taiga.projects.wiki.api import WikiViewSet
from taiga.projects.wiki.api import WikiLinkViewSet
from taiga.projects.wiki.api import WikiWatchersViewSet

router.register(r"milestones", MilestoneViewSet, base_name="milestones")
router.register(r"milestones/(?P<resource_id>\d+)/watchers", MilestoneWatchersViewSet, base_name="milestone-watchers")
router.register(r"userstories", UserStoryViewSet, base_name="userstories")
router.register(r"userstories/(?P<resource_id>\d+)/voters", UserStoryVotersViewSet, base_name="userstory-voters")
router.register(r"userstories/(?P<resource_id>\d+)/watchers", UserStoryWatchersViewSet, base_name="userstory-watchers")
router.register(r"tasks", TaskViewSet, base_name="tasks")
router.register(r"tasks/(?P<resource_id>\d+)/voters", TaskVotersViewSet, base_name="task-voters")
router.register(r"tasks/(?P<resource_id>\d+)/watchers", TaskWatchersViewSet, base_name="task-watchers")
router.register(r"issues", IssueViewSet, base_name="issues")
router.register(r"issues/(?P<resource_id>\d+)/voters", IssueVotersViewSet, base_name="issue-voters")
router.register(r"issues/(?P<resource_id>\d+)/watchers", IssueWatchersViewSet, base_name="issue-watchers")
router.register(r"wiki", WikiViewSet, base_name="wiki")
router.register(r"wiki/(?P<resource_id>\d+)/watchers", WikiWatchersViewSet, base_name="wiki-watchers")
router.register(r"wiki-links", WikiLinkViewSet, base_name="wiki-links")




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
from taiga.timeline.api import ProfileTimeline
from taiga.timeline.api import UserTimeline
from taiga.timeline.api import ProjectTimeline

router.register(r"timeline/profile", ProfileTimeline, base_name="profile-timeline")
router.register(r"timeline/user", UserTimeline, base_name="user-timeline")
router.register(r"timeline/project", ProjectTimeline, base_name="project-timeline")


# Webhooks
from taiga.webhooks.api import WebhookViewSet
from taiga.webhooks.api import WebhookLogViewSet

router.register(r"webhooks", WebhookViewSet, base_name="webhooks")
router.register(r"webhooklogs", WebhookLogViewSet, base_name="webhooklogs")


# GitHub webhooks
from taiga.hooks.github.api import GitHubViewSet

router.register(r"github-hook", GitHubViewSet, base_name="github-hook")


# Gitlab webhooks
from taiga.hooks.gitlab.api import GitLabViewSet

router.register(r"gitlab-hook", GitLabViewSet, base_name="gitlab-hook")


# Bitbucket webhooks
from taiga.hooks.bitbucket.api import BitBucketViewSet

router.register(r"bitbucket-hook", BitBucketViewSet, base_name="bitbucket-hook")


# Gogs webhooks
from taiga.hooks.gogs.api import GogsViewSet

router.register(r"gogs-hook", GogsViewSet, base_name="gogs-hook")


# Importer
from taiga.export_import.api import ProjectImporterViewSet, ProjectExporterViewSet

router.register(r"importer", ProjectImporterViewSet, base_name="importer")
router.register(r"exporter", ProjectExporterViewSet, base_name="exporter")


# External apps
from taiga.external_apps.api import Application, ApplicationToken
router.register(r"applications", Application, base_name="applications")
router.register(r"application-tokens", ApplicationToken, base_name="application-tokens")



# Stats
#   - see taiga.stats.routers and taiga.stats.apps


# Feedback
#   - see taiga.feedback.routers and taiga.feedback.apps
