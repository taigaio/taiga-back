# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import re
import markdown

from markdown.treeprocessors import Treeprocessor

from taiga.front.templatetags.functions import resolve


class TargetBlankLinkExtension(markdown.Extension):
    """An extension that add target="_blank" to all external links."""
    def extendMarkdown(self, md):
        md.treeprocessors.register(TargetBlankLinksTreeprocessor(md),
                                   "target_blank_links",
                                   10)


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
