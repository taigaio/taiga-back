# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re
import os.path

from taiga.hooks.event_hooks import BasePushEventHook


class BaseGogsEventHook():
    platform = "Gogs"
    platform_slug = "gogs"

    def replace_gogs_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = fr"\g<1>[Gogs#\g<2>]({project_url}/issues/\g<2>)\g<3>"
        return re.sub(r"(\s|^)#(\d+)(\s|$)", template, wiki_text, 0, re.M)


class PushEventHook(BaseGogsEventHook, BasePushEventHook):
    def get_data(self):
        result = []
        commits = self.payload.get("commits", [])
        project_url = self.payload.get("repository", {}).get("html_url", "")

        for commit in filter(None, commits):
            user_name = commit.get('author', {}).get('username', "")
            result.append({
                "user_id": user_name,
                "user_name": user_name,
                "user_url": os.path.join(os.path.dirname(os.path.dirname(project_url)), user_name),
                "commit_id": commit.get("id", None),
                "commit_url": commit.get("url", None),
                "commit_message": commit.get("message").strip(),
                "commit_short_message": commit.get("message").split("\n")[0].strip(),
            })
        return result
