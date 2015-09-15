# -*- coding: utf-8 -*-

# Tested on Markdown 2.3.1
#
# Copyright (c) 2014, Esteban Castro Borsani
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString

from taiga.users.models import User


class MentionsExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        MENTION_RE = r'(@)([a-zA-Z0-9.-\.]+)'
        mentionsPattern = MentionsPattern(MENTION_RE)
        mentionsPattern.md = md
        md.inlinePatterns.add('mentions', mentionsPattern, '_end')


class MentionsPattern(Pattern):
    def handleMatch(self, m):
        username = m.group(3)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return "@{}".format(username)

        url = "/profile/{}".format(username)

        link_text = "@{}".format(username)

        a = etree.Element('a')
        a.text = AtomicString(link_text)

        a.set('href', url)
        a.set('title', user.get_full_name())
        a.set('class', "mention")

        self.md.extracted_data['mentions'].append(user)

        return a
