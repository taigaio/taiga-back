# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# Copyright (C) 2014 Anler Hernández <hello@anler.me>
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
from markdown.util import etree

from taiga.front import resolve


class WikiLinkExtension(Extension):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        return super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        WIKILINK_RE = r"\[\[([\w0-9_ -]+)(\|[\w0-9_ -]+)?\]\]"
        wikilinkPattern = WikiLinksPattern(WIKILINK_RE, self.project)
        wikilinkPattern.md = md
        md.inlinePatterns.add("wikilink", wikilinkPattern, "<not_strong")


class WikiLinksPattern(Pattern):
    def __init__(self, pattern, project):
        self.project = project
        super().__init__(pattern)

    def handleMatch(self, m):
        label = m.group(2).strip()
        url = resolve("wiki", self.project.slug, label)

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
