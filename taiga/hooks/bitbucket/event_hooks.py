# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re

from taiga.hooks.event_hooks import (BaseIssueEventHook, BaseIssueCommentEventHook, BasePushEventHook,
                                     ISSUE_ACTION_CREATE, ISSUE_ACTION_UPDATE, ISSUE_ACTION_DELETE)


class BaseBitBucketEventHook():
    platform = "BitBucket"
    platform_slug = "bitbucket"

    def replace_bitbucket_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = fr"\g<1>[BitBucket#\g<2>]({project_url}/issues/\g<2>)\g<3>"
        return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class IssuesEventHook(BaseBitBucketEventHook, BaseIssueEventHook):
    @property
    def action_type(self):
        # NOTE: Only CREATE for now
        return ISSUE_ACTION_CREATE

    def get_data(self):
        description = self.payload.get('issue', {}).get('content', {}).get('raw', '')
        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)
        return {
            "number": self.payload.get('issue', {}).get('id', None),
            "subject": self.payload.get('issue', {}).get('title', None),
            "url": self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None),
            "user_id": self.payload.get('actor', {}).get('uuid', None),
            "user_name": self.payload.get('actor', {}).get('nickname', None),
            "user_url": self.payload.get('actor', {}).get('links', {}).get('html', {}).get('href'),
            "description": self.replace_bitbucket_references(project_url, description),
        }


class IssueCommentEventHook(BaseBitBucketEventHook, BaseIssueCommentEventHook):
    def get_data(self):
        comment_message = self.payload.get('comment', {}).get('content', {}).get('raw', '')
        project_url = self.payload.get('repository', {}).get('links', {}).get('html', {}).get('href', None)
        issue_url = self.payload.get('issue', {}).get('links', {}).get('html', {}).get('href', None)
        comment_id = self.payload.get('comment', {}).get('id', None)
        comment_url = f"{issue_url}#comment-{comment_id}"
        return {
            "number": self.payload.get('issue', {}).get('id', None),
            'url': issue_url,
            'user_id': self.payload.get('actor', {}).get('uuid', None),
            'user_name': self.payload.get('actor', {}).get('nickname', None),
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
                    "user_name": commit.get('author', {}).get('user', {}).get('nickname', None),
                    "user_url": commit.get('author', {}).get('user', {}).get('links', {}).get('html', {}).get('href'),
                    "commit_id": commit.get("hash", None),
                    "commit_url": commit.get("links", {}).get('html', {}).get('href'),
                    "commit_message": message.strip(),
                    "commit_short_message": message.split("\n")[0].strip(),
                })
        return result
