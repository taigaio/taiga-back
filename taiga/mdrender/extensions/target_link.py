# -*- coding: utf-8 -*-
# Copyright (C) 2014-2017 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2017 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2017 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2017 Alejandro Alonso <alejandro.alonso@kaleidos.net>
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
import markdown

from markdown.treeprocessors import Treeprocessor

from taiga.front.templatetags.functions import resolve


class TargetBlankLinkExtension(markdown.Extension):
    """An extension that add target="_blank" to all external links."""
    def extendMarkdown(self, md):
        md.treeprocessors.add("target_blank_links",
                              TargetBlankLinksTreeprocessor(md),
                              "<prettify")


class TargetBlankLinksTreeprocessor(Treeprocessor):
    def run(self, root):
        home_url = resolve("home")
        links = root.iter("a")
        for a in links:
            href = a.get("href", "")
            url = a.get("href", "")
            if url.endswith("/"):
                url = url[:-1]

            if not url.startswith(home_url):
                a.set("target", "_blank")
