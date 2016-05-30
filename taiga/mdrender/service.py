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

import hashlib
import functools
import bleach

# BEGIN PATCH
import html5lib
from html5lib.serializer.htmlserializer import HTMLSerializer


def _serialize(domtree):
    walker = html5lib.treewalkers.getTreeWalker('etree')
    stream = walker(domtree)
    serializer = HTMLSerializer(quote_attr_values=True,
                                omit_optional_tags=False,
                                alphabetical_attributes=True)

    return serializer.render(stream)

bleach._serialize = _serialize
# END PATCH

from django.core.cache import cache
from django.utils.encoding import force_bytes

from markdown import Markdown

from .extensions.autolink import AutolinkExtension
from .extensions.automail import AutomailExtension
from .extensions.semi_sane_lists import SemiSaneListExtension
from .extensions.spaced_link import SpacedLinkExtension
from .extensions.strikethrough import StrikethroughExtension
from .extensions.wikilinks import WikiLinkExtension
from .extensions.emojify import EmojifyExtension
from .extensions.mentions import MentionsExtension
from .extensions.references import TaigaReferencesExtension
from .extensions.target_link import TargetBlankLinkExtension

# Bleach configuration
bleach.ALLOWED_TAGS += ["p", "table", "thead", "tbody", "th", "tr", "td", "h1",
                        "h2", "h3", "h4", "h5", "h6", "div", "pre", "span",
                        "hr", "dl", "dt", "dd", "sup", "img", "del", "br",
                        "ins"]

bleach.ALLOWED_STYLES.append("background")

bleach.ALLOWED_ATTRIBUTES["a"] = ["href", "title", "alt", "target"]
bleach.ALLOWED_ATTRIBUTES["img"] = ["alt", "src"]
bleach.ALLOWED_ATTRIBUTES["*"] = ["class", "style", "id"]


def _make_extensions_list(project=None):
    return [AutolinkExtension(),
            AutomailExtension(),
            SemiSaneListExtension(),
            SpacedLinkExtension(),
            StrikethroughExtension(),
            WikiLinkExtension(project),
            EmojifyExtension(),
            MentionsExtension(),
            TaigaReferencesExtension(project),
            TargetBlankLinkExtension(),
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.sane_lists",
            "markdown.extensions.toc",
            "markdown.extensions.nl2br"]


import diff_match_patch


def cache_by_sha(func):
    @functools.wraps(func)
    def _decorator(project, text):
        sha1_hash = hashlib.sha1(force_bytes(text)).hexdigest()
        key = "{}-{}".format(sha1_hash, project.id)

        # Try to get it from the cache
        cached = cache.get(key)
        if cached is not None:
            return cached

        returned_value = func(project, text)
        cache.set(key, returned_value, timeout=None)
        return returned_value

    return _decorator


def _get_markdown(project):
    extensions = _make_extensions_list(project=project)
    md = Markdown(extensions=extensions)
    md.extracted_data = {"mentions": [], "references": []}
    return md


@cache_by_sha
def render(project, text):
    md = _get_markdown(project)
    return bleach.clean(md.convert(text))


def render_and_extract(project, text):
    md = _get_markdown(project)
    result = bleach.clean(md.convert(text))
    return (result, md.extracted_data)


class DiffMatchPatch(diff_match_patch.diff_match_patch):
    def diff_pretty_html(self, diffs):
        html = []
        for (op, data) in diffs:
            text = (data.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace("\n", "<br />"))
            if op == self.DIFF_INSERT:
                html.append("<ins style=\"background:#e6ffe6;\">%s</ins>" % text)
            elif op == self.DIFF_DELETE:
                html.append("<del style=\"background:#ffe6e6;\">%s</del>" % text)
            elif op == self.DIFF_EQUAL:
                html.append("<span>%s</span>" % text)
        return "".join(html)


def get_diff_of_htmls(html1, html2):
    diffutil = DiffMatchPatch()
    diffs = diffutil.diff_main(html1, html2)
    diffutil.diff_cleanupSemantic(diffs)
    return diffutil.diff_pretty_html(diffs)


__all__ = ["render", "get_diff_of_htmls", "render_and_extract"]
