# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re

from taiga.hooks.event_hooks import (BaseIssueEventHook, BaseIssueCommentEventHook, BasePushEventHook,
                                     ISSUE_ACTION_CREATE, ISSUE_ACTION_UPDATE, ISSUE_ACTION_CLOSE,
                                     ISSUE_ACTION_REOPEN)


class BaseGitHubEventHook():
    platform = "GitHub"
    platform_slug = "github"

    def replace_github_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = fr"\g<1>[GitHub#\g<2>]({project_url}/issues/\g<2>)\g<3>"
        return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseGitHubEventHook, BaseIssueEventHook):
    _ISSUE_ACTIONS = {
      "opened": ISSUE_ACTION_CREATE,
      "edited": ISSUE_ACTION_UPDATE,
      "closed": ISSUE_ACTION_CLOSE,
      "reopened": ISSUE_ACTION_REOPEN,
    }

    @property
    def action_type(self):
        _action = self.payload.get('action', '')
        return self._ISSUE_ACTIONS.get(_action, None)

    def ignore(self):
        return self.action_type not in [
            ISSUE_ACTION_CREATE,
            ISSUE_ACTION_UPDATE,
            ISSUE_ACTION_CLOSE,
            ISSUE_ACTION_REOPEN,
        ]

    def get_data(self):
        description = self.payload.get('issue', {}).get('body', None)
        project_url = self.payload.get('repository', {}).get('html_url', None)
        state = self.payload.get('issue', {}).get('state', 'open')

        return {
            "number": self.payload.get('issue', {}).get('number', None),
            "subject": self.payload.get('issue', {}).get('title', None),
            "url": self.payload.get('issue', {}).get('html_url', None),
            "user_id": self.payload.get('sender', {}).get('id', None),
            "user_name": self.payload.get('sender', {}).get('login', None),
            "user_url": self.payload.get('sender', {}).get('html_url', None),
            "description": self.replace_github_references(project_url, description),
            "status": self.close_status if state == "closed" else self.open_status,
        }


class IssueCommentEventHook(BaseGitHubEventHook, BaseIssueCommentEventHook):
    def ignore(self):
        return self.payload.get('action', None) != "created"

    def get_data(self):
        comment_message = self.payload.get('comment', {}).get('body', None)
        project_url = self.payload.get('repository', {}).get('html_url', None)
        return {
            "number": self.payload.get('issue', {}).get('number', None),
            "url": self.payload.get('issue', {}).get('html_url', None),
            "user_id": self.payload.get('sender', {}).get('id', None),
            "user_name": self.payload.get('sender', {}).get('login', None),
            "user_url": self.payload.get('sender', {}).get('html_url', None),
            "comment_url": self.payload.get('comment', {}).get('html_url', None),
            "comment_message": self.replace_github_references(project_url, comment_message),
        }


class PushEventHook(BaseGitHubEventHook, BasePushEventHook):
    def get_data(self):
        result = []
        github_user = self.payload.get('sender', {})
        commits = self.payload.get("commits", [])
        for commit in filter(None, commits):
            result.append({
                "user_id": github_user.get('id', None),
                "user_name": github_user.get('login', None),
                "user_url": github_user.get('html_url', None),
                "commit_id": commit.get("id", None),
                "commit_url": commit.get("url", None),
                "commit_message": commit.get("message").strip(),
                "commit_short_message": commit.get("message").split("\n")[0].strip(),
            })

        return result
