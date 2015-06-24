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

        # In bitbucket the payload is a list! :(
        for payload_element_text in self.payload:
            try:
                payload_element = json.loads(payload_element_text)
            except ValueError:
                raise exc.BadRequest(_("The payload is not valid"))

            commits = payload_element.get("commits", [])
            for commit in commits:
                message = commit.get("message", None)
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
