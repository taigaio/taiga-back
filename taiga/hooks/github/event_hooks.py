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

from taiga.hooks.event_hooks import BaseNewIssueEventHook, BaseIssueCommentEventHook, BasePushEventHook


class BaseGitHubEventHook():
    platform = "GitHub"
    platform_slug = "github"

    def replace_github_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = "\g<1>[GitHub#\g<2>]({}/issues/\g<2>)\g<3>".format(project_url)
        return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseGitHubEventHook, BaseNewIssueEventHook):
    def ignore(self):
        return self.payload.get('action', None) != "opened"

    def get_data(self):
        description = self.payload.get('issue', {}).get('body', None)
        project_url = self.payload.get('repository', {}).get('html_url', None)
        return {
            "number": self.payload.get('issue', {}).get('number', None),
            "subject": self.payload.get('issue', {}).get('title', None),
            "url": self.payload.get('issue', {}).get('html_url', None),
            "user_id": self.payload.get('issue', {}).get('user', {}).get('id', None),
            "user_name": self.payload.get('issue', {}).get('user', {}).get('login', None),
            "user_url": self.payload.get('issue', {}).get('user', {}).get('html_url', None),
            "description": self.replace_github_references(project_url, description),
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
                "commit_message": commit.get("message", None),
            })

        return result
