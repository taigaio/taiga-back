# Copyright (C) 2014-2016 Andrey Antukh <niwi@niwi.nz>
# Copyright (C) 2014-2016 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014-2016 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014-2016 Alejandro Alonso <alejandro.alonso@kaleidos.net>
# Copyright (C) 2014-2016 Anler Hernández <hello@anler.me>
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

from markdown import Extension
from markdown.inlinepatterns import Pattern
from markdown.treeprocessors import Treeprocessor

from markdown.util import etree

from taiga.front.templatetags.functions import resolve
from taiga.base.utils.slug import slugify

import re


class WikiLinkExtension(Extension):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        return super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        WIKILINK_RE = r"\[\[([\w0-9_ -]+)(\|[^\]]+)?\]\]"
        md.inlinePatterns.add("wikilinks",
                              WikiLinksPattern(md, WIKILINK_RE, self.project),
                              "<not_strong")
        md.treeprocessors.add("relative_to_absolute_links",
                              RelativeLinksTreeprocessor(md, self.project),
                              "<prettify")


class WikiLinksPattern(Pattern):
    def __init__(self, md, pattern, project):
        self.project = project
        self.md = md
        super().__init__(pattern)

    def handleMatch(self, m):
        label = m.group(2).strip()
        url = resolve("wiki", self.project.slug, slugify(label))

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
        links = root.getiterator("a")
        for a in links:
            href = a.get("href", "")

            if SLUG_RE.search(href):
                # [wiki](wiki_page) -> <a href="FRONT_HOST/.../wiki/wiki_page" ...
                url = resolve("wiki", self.project.slug, href)
                a.set("href", url)
                a.set("class", "reference wiki")

            elif href and href[0] == "/":
                # [some link](/some/link) -> <a href="FRONT_HOST/some/link" ...
                url = "{}{}".format(resolve("home"), href[1:])
                a.set("href", url)
