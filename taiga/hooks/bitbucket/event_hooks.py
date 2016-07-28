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


class BaseBitBucketEventHook():
    platform = "BitBucket"
    platform_slug = "bitbucket"

    def replace_bitbucket_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = "\g<1>[BitBucket#\g<2>]({}/issues/\g<2>)\g<3>".format(project_url)
        return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseBitBucketEventHook, BaseNewIssueEventHook):
    def get_data(self):
        description = self.payload.get('issue', {}).get('content', {}).get('raw', '')
        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)
        return {
            "number": self.payload.get('issue', {}).get('id', None),
            "subject": self.payload.get('issue', {}).get('title', None),
            "url": self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None),
            "user_id": self.payload.get('actor', {}).get('uuid', None),
            "user_name": self.payload.get('actor', {}).get('username', None),
            "user_url": self.payload.get('actor', {}).get('links', {}).get('html', {}).get('href'),
            "description": self.replace_bitbucket_references(project_url, description),
        }


class IssueCommentEventHook(BaseBitBucketEventHook, BaseIssueCommentEventHook):
    def get_data(self):
        comment_message = self.payload.get('comment', {}).get('content', {}).get('raw', '')
        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)
        issue_url = self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None)
        comment_id = self.payload.get('comment', {}).get('id', None)
        comment_url = "{}#comment-{}".format(issue_url, comment_id)
        return {
            "number": self.payload.get('issue', {}).get('id', None),
            'url': issue_url,
            'user_id': self.payload.get('actor', {}).get('uuid', None),
            'user_name': self.payload.get('actor', {}).get('username', None),
            'user_url': self.payload.get('actor', {}).get('links', {}).get('html', {}).get('href'),
            'comment_url': comment_url,
            'comment_message': self.replace_bitbucket_references(project_url, comment_message)
        }


class PushEventHook(BaseBitBucketEventHook, BasePushEventHook):
    def get_data(self):
        result = []
        changes = self.payload.get("push", {}).get('changes', [])
        for change in filter(None, changes):
            for commit in change.get("commits", []):
                message = commit.get("message")
                result.append({
                    'user_id': commit.get('author', {}).get('user', {}).get('uuid', None),
                    "user_name": commit.get('author', {}).get('user', {}).get('username', None),
                    "user_url": commit.get('author', {}).get('user', {}).get('links', {}).get('html', {}).get('href'),
                    "commit_id": commit.get("hash", None),
                    "commit_url": commit.get("links", {}).get('html', {}).get('href'),
                    "commit_message": message.strip(),
                })
        return result
