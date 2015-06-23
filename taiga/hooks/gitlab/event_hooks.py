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

import re
import os

from django.utils.translation import ugettext as _

from taiga.projects.models import IssueStatus, TaskStatus, UserStoryStatus

from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.history.services import take_snapshot
from taiga.projects.notifications.services import send_notifications
from taiga.hooks.event_hooks import BaseEventHook
from taiga.hooks.exceptions import ActionSyntaxException

from .services import get_gitlab_user


class PushEventHook(BaseEventHook):
    def process_event(self):
        if self.payload is None:
            return

        commits = self.payload.get("commits", [])
        for commit in commits:
            message = commit.get("message", None)
            self._process_message(message, None)

    def _process_message(self, message, gitlab_user):
        """
          The message we will be looking for seems like
            TG-XX #yyyyyy
          Where:
            XX: is the ref for us, issue or task
            yyyyyy: is the status slug we are setting
        """
        if message is None:
            return

        p = re.compile("tg-(\d+) +#([-\w]+)")
        for m in p.finditer(message.lower()):
            ref = m.group(1)
            status_slug = m.group(2)
            self._change_status(ref, status_slug, gitlab_user)

    def _change_status(self, ref, status_slug, gitlab_user):
        if Issue.objects.filter(project=self.project, ref=ref).exists():
            modelClass = Issue
            statusClass = IssueStatus
        elif Task.objects.filter(project=self.project, ref=ref).exists():
            modelClass = Task
            statusClass = TaskStatus
        elif UserStory.objects.filter(project=self.project, ref=ref).exists():
            modelClass = UserStory
            statusClass = UserStoryStatus
        else:
            raise ActionSyntaxException(_("The referenced element doesn't exist"))

        element = modelClass.objects.get(project=self.project, ref=ref)

        try:
            status = statusClass.objects.get(project=self.project, slug=status_slug)
        except statusClass.DoesNotExist:
            raise ActionSyntaxException(_("The status doesn't exist"))

        element.status = status
        element.save()

        snapshot = take_snapshot(element,
                                 comment=_("Status changed from GitLab commit"),
                                 user=get_gitlab_user(gitlab_user))
        send_notifications(element, history=snapshot)


def replace_gitlab_references(project_url, wiki_text):
    if wiki_text == None:
        wiki_text = ""

    template = "\g<1>[GitLab#\g<2>]({}/issues/\g<2>)\g<3>".format(project_url)
    return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseEventHook):
    def process_event(self):
        if self.payload.get('object_attributes', {}).get("action", "") != "open":
            return

        subject = self.payload.get('object_attributes', {}).get('title', None)
        description = self.payload.get('object_attributes', {}).get('description', None)
        gitlab_reference = self.payload.get('object_attributes', {}).get('url', None)

        project_url = None
        if gitlab_reference:
            project_url = os.path.basename(os.path.basename(gitlab_reference))

        if not all([subject, gitlab_reference, project_url]):
            raise ActionSyntaxException(_("Invalid issue information"))

        issue = Issue.objects.create(
            project=self.project,
            subject=subject,
            description=replace_gitlab_references(project_url, description),
            status=self.project.default_issue_status,
            type=self.project.default_issue_type,
            severity=self.project.default_severity,
            priority=self.project.default_priority,
            external_reference=['gitlab', gitlab_reference],
            owner=get_gitlab_user(None)
        )
        take_snapshot(issue, user=get_gitlab_user(None))

        snapshot = take_snapshot(issue, comment=_("Created from GitLab"), user=get_gitlab_user(None))
        send_notifications(issue, history=snapshot)
