# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re

from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from taiga.projects.models import IssueStatus, TaskStatus, UserStoryStatus, EpicStatus, ProjectModulesConfig
from taiga.projects.epics.models import Epic
from taiga.projects.issues.models import Issue
from taiga.projects.tasks.models import Task
from taiga.projects.userstories.models import UserStory
from taiga.projects.history.services import take_snapshot
from taiga.projects.notifications.services import send_notifications
from taiga.hooks.exceptions import ActionSyntaxException
from taiga.users.models import AuthData

from taiga.base.utils import json


ISSUE_ACTION_CREATE = "ISSUE_CREATE"
ISSUE_ACTION_UPDATE = "ISSUE_UPDATE"
ISSUE_ACTION_DELETE = "ISSUE_DELETE"
ISSUE_ACTION_CLOSE = "ISSUE_CLOSE"
ISSUE_ACTION_REOPEN = "ISSUE_REOPEN"


class BaseEventHook:
    platform = "Unknown"
    platform_slug = "unknown"

    def __init__(self, project, payload):
        self.project = project
        self.payload = payload

    @property
    def config(self):
        if hasattr(self.project, "modules_config"):
            return self.project.modules_config.config.get(self.platform_slug, {})
        return {}

    def ignore(self):
        return False

    def get_user(self, user_id, platform=None):
        user = None

        if user_id:
            try:
                user = AuthData.objects.get(key=platform, value=user_id).user
            except AuthData.DoesNotExist:
                pass

        if user is None and platform is not None:
            user = get_user_model().objects.get(is_system=True, username__startswith=platform)

        return user


class BaseIssueCommentEventHook(BaseEventHook):
    def get_data(self):
        raise NotImplementedError

    def generate_issue_comment_message(self, **kwargs):
        _issue_comment_message = _(
            "[{user_name}]({user_url} "
            "\"See {user_name}'s {platform} profile\") "
            "says in [{platform}#{number}]({comment_url} \"Go to comment\"):\n\n"
            "\"{comment_message}\""
        )
        _simple_issue_comment_message = _("Comment From {platform}:\n\n> {comment_message}")
        try:
            return _issue_comment_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_issue_comment_message.format(platform=self.platform, message=kwargs.get("comment_message"))

    def process_event(self):
        if self.ignore():
            return

        data = self.get_data()

        if not all([data["comment_message"], data["url"]]):
            raise ActionSyntaxException(_("Invalid issue comment information"))

        comment = self.generate_issue_comment_message(**data)

        issues = Issue.objects.filter(external_reference=[self.platform_slug, data["url"]])
        tasks = Task.objects.filter(external_reference=[self.platform_slug, data["url"]])
        uss = UserStory.objects.filter(external_reference=[self.platform_slug, data["url"]])

        for item in list(issues) + list(tasks) + list(uss):
            snapshot = take_snapshot(item, comment=comment, user=self.get_user(data["user_id"], self.platform_slug))
            send_notifications(item, history=snapshot)


class BaseIssueEventHook(BaseEventHook):
    @property
    def action_type(self):
        raise NotImplementedError

    @property
    def open_status(self):
        return self.project.default_issue_status

    @property
    def close_status(self):
        close_status = self.config.get("close_status", None)

        if close_status:
            try:
                return self.project.issue_statuses.get(id=close_status)
            except IssueStatus.DoesNotExist:
                pass

        return self.project.issue_statuses.filter(is_closed=True).order_by("order").first()

    def get_data(self):
        raise NotImplementedError

    def get_issue(self, data):
        try:
            return Issue.objects.get(project=self.project,
                                     external_reference=[self.platform_slug, data["url"]])
        except Issue.DoesNotExist:
            return None

    def generate_create_issue_comment(self, **kwargs):
        _new_issue_message = _(
            "Issue created by [{user_name}]({user_url} "
            "\"See {user_name}'s {platform} profile\") "
            "from [{platform}#{number}]({url} \"Go to issue\")."
        )
        _simple_new_issue_message = _("Issue created from {platform}.")
        try:
            return _new_issue_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_new_issue_message.format(platform=self.platform)

    def generate_update_issue_comment(self, **kwargs):
        _edit_issue_message = _(
            "Issue modified by [{user_name}]({user_url} "
            "\"See {user_name}'s {platform} profile\") "
            "from [{platform}#{number}]({url} \"Go to issue\")."
        )
        _simple_edit_issue_message = _("Issue modified from {platform}.")
        try:
            return _edit_issue_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_edit_issue_message.format(platform=self.platform)

    def generate_close_issue_comment(self, **kwargs):
        _edit_issue_message = _(
            "Issue closed by [{user_name}]({user_url} "
            "\"See {user_name}'s {platform} profile\") "
            "from [{platform}#{number}]({url} \"Go to issue\")."
        )
        _simple_edit_issue_message = _("Issue closed from {platform}.")
        try:
            return _edit_issue_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_edit_issue_message.format(platform=self.platform)

    def generate_reopen_issue_comment(self, **kwargs):
        _edit_issue_message = _(
            "Issue reopened by [{user_name}]({user_url} "
            "\"See {user_name}'s {platform} profile\") "
            "from [{platform}#{number}]({url} \"Go to issue\")."
        )
        _simple_edit_issue_message = _("Issue reopened from {platform}.")
        try:
            return _edit_issue_message.format(platform=self.platform, **kwargs)
        except Exception:
            return _simple_edit_issue_message.format(platform=self.platform)

    def _create_issue(self, data):
        user = self.get_user(data["user_id"], self.platform_slug)

        issue = Issue.objects.create(
            project=self.project,
            subject=data["subject"],
            description=data["description"],
            status=data.get("status", self.project.default_issue_status),
            type=self.project.default_issue_type,
            severity=self.project.default_severity,
            priority=self.project.default_priority,
            external_reference=[self.platform_slug, data['url']],
            owner=user
        )
        take_snapshot(issue, user=user)

        comment = self.generate_create_issue_comment(**data)

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)

    def _update_issue(self, data):
        issue = self.get_issue(data)

        if not issue:
            # The issue is not created yet, add it
            return self._create_issue(data)

        user = self.get_user(data["user_id"], self.platform_slug)

        issue.subject = data["subject"]
        issue.description = data["description"]
        issue.save()

        comment = self.generate_update_issue_comment(**data)

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)

    def _close_issue(self, data):
        issue = self.get_issue(data)

        if not issue:
            # The issue is not created yet, add it
            return self._create_issue(data)

        if not self.close_status:
            return

        user = self.get_user(data["user_id"], self.platform_slug)

        issue.status = self.close_status
        issue.save()

        comment = self.generate_close_issue_comment(**data)

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)

    def _reopen_issue(self, data):
        issue = self.get_issue(data)

        if not issue:
            # The issue is not created yet, add it
            return self._create_issue(data)

        if not self.open_status:
            return

        user = self.get_user(data["user_id"], self.platform_slug)

        issue.status = self.open_status
        issue.save()

        comment = self.generate_reopen_issue_comment(**data)

        snapshot = take_snapshot(issue, comment=comment, user=user)
        send_notifications(issue, history=snapshot)

    def _delete_issue(self, data):
        raise NotImplementedError

    def process_event(self):
        if self.ignore():
            return

        data = self.get_data()

        if not all([data["subject"], data["url"]]):
            raise ActionSyntaxException(_("Invalid issue information"))

        if self.action_type == ISSUE_ACTION_CREATE:
            self._create_issue(data)
        elif self.action_type == ISSUE_ACTION_UPDATE:
            self._update_issue(data)
        elif self.action_type == ISSUE_ACTION_CLOSE:
            self._close_issue(data)
        elif self.action_type == ISSUE_ACTION_REOPEN:
            self._reopen_issue(data)
        elif self.action_type == ISSUE_ACTION_DELETE:
            self._delete_issue(data)
        else:
            raise NotImplementedError


class BasePushEventHook(BaseEventHook):
    def get_data(self):
        raise NotImplementedError

    def generate_status_change_comment(self, **kwargs):
        if kwargs.get("user_url", None) is None:
            user_text = kwargs.get("user_name", _("unknown user"))
        else:
            user_text = "[{user_name}]({user_url} \"See {user_name}'s {platform} profile\")".format(
                platform=self.platform,
                **kwargs
            )
        _status_change_message = _(
            "{user_text} changed the status from "
            "[{platform} commit]({commit_url} \"See commit '{commit_id} - {commit_short_message}'\")\n\n"
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
        if kwargs.get("user_url", None) is None:
            user_text = kwargs.get("user_name", _("unknown user"))
        else:
            user_text = "[{user_name}]({user_url} \"See {user_name}'s {platform} profile\")".format(
                platform=self.platform,
                **kwargs
            )

        _status_change_message = _(
            "This {type_name} has been mentioned by {user_text} "
            "in the [{platform} commit]({commit_url} \"See commit '{commit_id} - {commit_short_message}'\") "
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
        if Epic.objects.filter(project=self.project, ref=ref).exists():
            modelClass = Epic
            statusClass = EpicStatus
        elif Issue.objects.filter(project=self.project, ref=ref).exists():
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
            p = re.compile(r"tg-(\d+) +#([-\w]+)")
            for m in p.finditer(commit['commit_message'].lower()):
                ref = m.group(1)
                status_slug = m.group(2)
                (element, src_status, dst_status) = self.set_item_status(ref, status_slug)

                comment = self.generate_status_change_comment(src_status=src_status, dst_status=dst_status, **commit)
                snapshot = take_snapshot(element,
                                         comment=comment,
                                         user=self.get_user(commit["user_id"], self.platform_slug))
                send_notifications(element, history=snapshot)
                consumed_refs.append(ref)

            # Reference on commit
            p = re.compile(r"tg-(\d+)")
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
