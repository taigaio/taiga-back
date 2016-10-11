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
import os.path

from taiga.hooks.event_hooks import BasePushEventHook


class BaseGogsEventHook():
    platform = "Gogs"
    platform_slug = "gogs"

    def replace_gogs_references(self, project_url, wiki_text):
        if wiki_text is None:
            wiki_text = ""

        template = "\g<1>[Gogs#\g<2>]({}/issues/\g<2>)\g<3>".format(project_url)
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
                "commit_message": commit.get("message", None),
            })
        return result
