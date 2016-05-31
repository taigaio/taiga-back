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

import re

from django.utils.translation import ugettext as _

from taiga.base import exceptions as exc
from taiga.projects.models import IssueStatus, TaskStatus, UserStoryStatus
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.history.services import take_snapshot
from taiga.projects.notifications.services import send_notifications
from taiga.hooks.event_hooks import BaseEventHook
from taiga.hooks.exceptions import ActionSyntaxException
from taiga.base.utils import json

from .services import get_bitbucket_user


class PushEventHook(BaseEventHook):
    def process_event(self):
        if self.payload is None:
            return

        changes = self.payload.get("push", {}).get('changes', [])
        for change in filter(None, changes):
            commits = change.get("commits", [])
            if not commits:
                continue

            for commit in commits:
                message = commit.get("message", None)
                if not message:
                    continue

                self._process_message(message, None)

    def _process_message(self, message, bitbucket_user):
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
            self._change_status(ref, status_slug, bitbucket_user)

    def _change_status(self, ref, status_slug, bitbucket_user):
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
                                 comment=_("Status changed from BitBucket commit"),
                                 user=get_bitbucket_user(bitbucket_user))
        send_notifications(element, history=snapshot)


def replace_bitbucket_references(project_url, wiki_text):
    template = "\g<1>[BitBucket#\g<2>]({}/issues/\g<2>)\g<3>".format(project_url)
    return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseEventHook):
    def process_event(self):
        number = self.payload.get('issue', {}).get('id', None)
        subject = self.payload.get('issue', {}).get('title', None)

        bitbucket_url = self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None)

        bitbucket_user_id = self.payload.get('actor', {}).get('user', {}).get('uuid', None)
        bitbucket_user_name = self.payload.get('actor', {}).get('user', {}).get('username', None)
        bitbucket_user_url = self.payload.get('actor', {}).get('user', {}).get('links', {}).get('html', {}).get('href')

        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)

        description = self.payload.get('issue', {}).get('content', {}).get('raw', '')
        description = replace_bitbucket_references(project_url, description)

        user = get_bitbucket_user(bitbucket_user_id)

        if not all([subject, bitbucket_url, project_url]):
            raise ActionSyntaxException(_("Invalid issue information"))

        issue = Issue.objects.create(
            project=self.project,
            subject=subject,
            description=description,
            status=self.project.default_issue_status,
            type=self.project.default_issue_type,
            severity=self.project.default_severity,
            priority=self.project.default_priority,
            external_reference=['bitbucket', bitbucket_url],
            owner=user
        )
        take_snapshot(issue, user=user)

        if number and subject and bitbucket_user_name and bitbucket_user_url:
            comment = _("Issue created by [@{bitbucket_user_name}]({bitbucket_user_url} "
                        "\"See @{bitbucket_user_name}'s BitBucket profile\") "
                        "from BitBucket.\nOrigin BitBucket issue: [bb#{number} - {subject}]({bitbucket_url} "
                        "\"Go to 'bb#{number} - {subject}'\"):\n\n"
                        "{description}").format(bitbucket_user_name=bitbucket_user_name,
                                                bitbucket_user_url=bitbucket_user_url,
                                                number=number,
                                                subject=subject,
                                                bitbucket_url=bitbucket_url,
                                                description=description)
        else:
            comment = _("Issue created from BitBucket.")

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)


class IssueCommentEventHook(BaseEventHook):
    def process_event(self):
        number = self.payload.get('issue', {}).get('id', None)
        subject = self.payload.get('issue', {}).get('title', None)

        bitbucket_url = self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None)
        bitbucket_user_id = self.payload.get('actor', {}).get('user', {}).get('uuid', None)
        bitbucket_user_name = self.payload.get('actor', {}).get('user', {}).get('username', None)
        bitbucket_user_url = self.payload.get('actor', {}).get('user', {}).get('links', {}).get('html', {}).get('href')

        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)

        comment_message = self.payload.get('comment', {}).get('content', {}).get('raw', '')
        comment_message = replace_bitbucket_references(project_url, comment_message)

        user = get_bitbucket_user(bitbucket_user_id)

        if not all([comment_message, bitbucket_url, project_url]):
            raise ActionSyntaxException(_("Invalid issue comment information"))

        issues = Issue.objects.filter(external_reference=["bitbucket", bitbucket_url])
        tasks = Task.objects.filter(external_reference=["bitbucket", bitbucket_url])
        uss = UserStory.objects.filter(external_reference=["bitbucket", bitbucket_url])

        for item in list(issues) + list(tasks) + list(uss):
            if number and subject and bitbucket_user_name and bitbucket_user_url:
                comment = _("Comment by [@{bitbucket_user_name}]({bitbucket_user_url} "
                            "\"See @{bitbucket_user_name}'s BitBucket profile\") "
                            "from BitBucket.\nOrigin BitBucket issue: [bb#{number} - {subject}]({bitbucket_url} "
                            "\"Go to 'bb#{number} - {subject}'\")\n\n"
                            "{message}").format(bitbucket_user_name=bitbucket_user_name,
                                                bitbucket_user_url=bitbucket_user_url,
                                                number=number,
                                                subject=subject,
                                                bitbucket_url=bitbucket_url,
                                                message=comment_message)
            else:
                comment = _("Comment From BitBucket:\n\n{message}").format(message=comment_message)

            snapshot = take_snapshot(item, comment=comment, user=user)
            send_notifications(item, history=snapshot)
