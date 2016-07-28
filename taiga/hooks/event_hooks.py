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
from django.contrib.auth import get_user_model
from taiga.projects.models import IssueStatus, TaskStatus, UserStoryStatus
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.history.services import take_snapshot
from taiga.projects.notifications.services import send_notifications
from taiga.hooks.exceptions import ActionSyntaxException
from taiga.users.models import AuthData


class BaseEventHook:
    platform = "Unknown"
    platform_slug = "unknown"

    def __init__(self, project, payload):
        self.project = project
        self.payload = payload

    def ignore(self):
        return False

    def get_user(self, user_id, platform):
        user = None

        if user_id:
            try:
                user = AuthData.objects.get(key=platform, value=user_id).user
            except AuthData.DoesNotExist:
                pass

        if user is None:
            user = get_user_model().objects.get(is_system=True, username__startswith=platform)

        return user


class BaseIssueCommentEventHook(BaseEventHook):
    def get_data(self):
        raise NotImplementedError

    def generate_issue_comment_message(self, **kwargs):
        _issue_comment_message = _(
            "[@{user_name}]({user_url} "
            "\"See @{user_name}'s {platform} profile\") "
            "says in [{platform}#{number}]({comment_url} \"Go to comment\"):\n\n"
            "\"{comment_message}\""
        )
        _simple_issue_comment_message = _("Comment From {platform}:\n\n> {comment_message}")
        try:
            return _issue_comment_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_issue_comment_message.format(platform=self.platform, message=kwargs.get('comment_message'))

    def process_event(self):
        if self.ignore():
            return

        data = self.get_data()

        if not all([data['comment_message'], data['url']]):
            raise ActionSyntaxException(_("Invalid issue comment information"))

        comment = self.generate_issue_comment_message(**data)

        issues = Issue.objects.filter(external_reference=[self.platform_slug, data['url']])
        tasks = Task.objects.filter(external_reference=[self.platform_slug, data['url']])
        uss = UserStory.objects.filter(external_reference=[self.platform_slug, data['url']])

        for item in list(issues) + list(tasks) + list(uss):
            snapshot = take_snapshot(item, comment=comment, user=self.get_user(data['user_id'], self.platform_slug))
            send_notifications(item, history=snapshot)


class BaseNewIssueEventHook(BaseEventHook):
    def get_data(self):
        raise NotImplementedError

    def generate_new_issue_comment(self, **kwargs):
        _new_issue_message = _(
            "Issue created by [@{user_name}]({user_url} "
            "\"See @{user_name}'s {platform} profile\") "
            "from [{platform}#{number}]({url} \"Go to issue\")."
        )
        _simple_new_issue_message = _("Issue created from {platform}.")
        try:
            return _new_issue_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_new_issue_message.format(platform=self.platform)

    def process_event(self):
        if self.ignore():
            return

        data = self.get_data()

        if not all([data['subject'], data['url']]):
            raise ActionSyntaxException(_("Invalid issue information"))

        user = self.get_user(data['user_id'], self.platform_slug)

        issue = Issue.objects.create(
            project=self.project,
            subject=data['subject'],
            description=data['description'],
            status=self.project.default_issue_status,
            type=self.project.default_issue_type,
            severity=self.project.default_severity,
            priority=self.project.default_priority,
            external_reference=[self.platform_slug, data['url']],
            owner=user
        )
        take_snapshot(issue, user=user)

        comment = self.generate_new_issue_comment(**data)

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)


class BasePushEventHook(BaseEventHook):
    def get_data(self):
        raise NotImplementedError

    def generate_status_change_comment(self, **kwargs):
        if kwargs.get('user_url', None) is None:
            user_text = kwargs.get('user_name', _('unknown user'))
        else:
            user_text = "[@{user_name}]({user_url} \"See @{user_name}'s {platform} profile\")".format(
                platform=self.platform,
                **kwargs
            )
        _status_change_message = _(
            "{user_text} changed the status from "
            "[{platform} commit]({commit_url} \"See commit '{commit_id} - {commit_message}'\")\n\n"
            "  - Status: **{src_status}** → **{dst_status}**"
        )
        _simple_status_change_message = _(
            "Changed status from {platform} commit.\n\n"
            " - Status: **{src_status}** → **{dst_status}**"
        )
        try:
            return _status_change_message.format(platform=self.platform, user_text=user_text, **kwargs)
        except Exception:
            return _simple_status_change_message.format(platform=self.platform)

    def generate_commit_reference_comment(self, **kwargs):
        if kwargs.get('user_url', None) is None:
            user_text = kwargs.get('user_name', _('unknown user'))
        else:
            user_text = "[@{user_name}]({user_url} \"See @{user_name}'s {platform} profile\")".format(
                platform=self.platform,
                **kwargs
            )

        _status_change_message = _(
            "This {type_name} has been mentioned by {user_text} "
            "in the [{platform} commit]({commit_url} \"See commit '{commit_id} - {commit_message}'\") "
            "\"{commit_message}\""
        )
        _simple_status_change_message = _(
            "This issue has been mentioned in the {platform} commit "
            "\"{commit_message}\""
        )
        try:
            return _status_change_message.format(platform=self.platform, user_text=user_text, **kwargs)
        except Exception:
            return _simple_status_change_message.format(platform=self.platform)

    def get_item_classes(self, ref):
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

        return (modelClass, statusClass)

    def get_item_by_ref(self, ref):
        (modelClass, statusClass) = self.get_item_classes(ref)

        return modelClass.objects.get(project=self.project, ref=ref)

    def set_item_status(self, ref, status_slug):
        (modelClass, statusClass) = self.get_item_classes(ref)
        element = modelClass.objects.get(project=self.project, ref=ref)

        try:
            status = statusClass.objects.get(project=self.project, slug=status_slug)
        except statusClass.DoesNotExist:
            raise ActionSyntaxException(_("The status doesn't exist"))

        src_status = element.status.name
        dst_status = status.name

        element.status = status
        element.save()
        return (element, src_status, dst_status)

    def process_event(self):
        if self.ignore():
            return
        data = self.get_data()

        for commit in data:
            consumed_refs = []

            # Status changes
            p = re.compile("tg-(\d+) +#([-\w]+)")
            for m in p.finditer(commit['commit_message'].lower()):
                ref = m.group(1)
                status_slug = m.group(2)
                (element, src_status, dst_status) = self.set_item_status(ref, status_slug)

                comment = self.generate_status_change_comment(src_status=src_status, dst_status=dst_status, **commit)
                snapshot = take_snapshot(element,
                                         comment=comment,
                                         user=self.get_user(commit['user_id'], self.platform_slug))
                send_notifications(element, history=snapshot)
                consumed_refs.append(ref)

            # Reference on commit
            p = re.compile("tg-(\d+)")
            for m in p.finditer(commit['commit_message'].lower()):
                ref = m.group(1)
                if ref in consumed_refs:
                    continue
                element = self.get_item_by_ref(ref)
                type_name = element.__class__._meta.verbose_name
                comment = self.generate_commit_reference_comment(type_name=type_name, **commit)
                snapshot = take_snapshot(element,
                                         comment=comment,
                                         user=self.get_user(commit['user_id'], self.platform_slug))
                send_notifications(element, history=snapshot)
                consumed_refs.append(ref)
