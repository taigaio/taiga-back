# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

from markdown import Extension
from markdown.inlinepatterns import Pattern
from markdown.treeprocessors import Treeprocessor
from xml.etree import ElementTree as etree

from taiga.front.templatetags.functions import resolve
from taiga.base.utils.slug import slugify

import re


class WikiLinkExtension(Extension):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        return super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        WIKILINK_RE = r"\[\[([\w0-9_ -]+)(\|[^\]]+)?\]\]"
        md.inlinePatterns.register(WikiLinksPattern(md, WIKILINK_RE, self.project),
                                   "wikilinks",
                                   20)
        md.treeprocessors.register(RelativeLinksTreeprocessor(md, self.project),
                                   "relative_to_absolute_links",
                                   20)


class WikiLinksPattern(Pattern):
    def __init__(self, md, pattern, project):
        self.project = project
        self.md = md
        super().__init__(pattern)

    def handleMatch(self, m):
        label = m.group(2).strip()

        # `project` could be other object (!)
        slug = getattr(self.project, "slug", None)
        if not slug:
            project = getattr(self.project, "project", None)
            slug = getattr(project, "slug", None)
            if not slug:
                return

        url = resolve("wiki", slug, slugify(label))

        if m.group(3):
            title = m.group(3).strip()[1:]
        else:
            title = label

        a = etree.Element("a")
        a.text = title
        a.set("href", url)
        a.set("title", title)
        a.set("class", "reference wiki")
        return a


SLUG_RE = re.compile(r"^[-a-zA-Z0-9_]+$")


class RelativeLinksTreeprocessor(Treeprocessor):
    def __init__(self, md, project):
        self.project = project
        super().__init__(md)

    def run(self, root):
        links = root.iter("a")
        for a in links:
            href = a.get("href", "")

            if SLUG_RE.search(href):
                # [wiki](wiki_page) -> <a href="FRONT_HOST/.../wiki/wiki_page" ...

                # `project` could be other object (!)
                slug = getattr(self.project, "slug", None)
                if not slug:
                    project = getattr(self.project, "project", None)
                    slug = getattr(project, "slug", None)
                    if not slug:
                        continue

                url = resolve("wiki", slug, href)
                a.set("href", url)
                a.set("class", "reference wiki")

            elif href and href[0] == "/":
                # [some link](/some/link) -> <a href="FRONT_HOST/some/link" ...
                url = "{}{}".format(resolve("home"), href[1:])
                a.set("href", url)
