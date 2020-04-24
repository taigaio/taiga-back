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
from django.contrib.auth import get_user_model

from markdown.extensions import Extension
from markdown.inlinepatterns import Pattern
from markdown.util import etree, AtomicString


class MentionsExtension(Extension):
    project = None

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        MENTION_RE = r"(@)([\w.-]+)"
        mentionsPattern = MentionsPattern(MENTION_RE, project=self.project)
        mentionsPattern.md = md
        md.inlinePatterns.add("mentions", mentionsPattern, "_end")


class MentionsPattern(Pattern):
    project = None

    def __init__(self, pattern, md=None, project=None):
        self.project = project
        super().__init__(pattern, md)

    def handleMatch(self, m):
        username = m.group(3)
        kwargs = {"username": username}
        if self.project is not None:
            kwargs["memberships__project_id"]=self.project.id
        try:
            user = get_user_model().objects.get(**kwargs)
        except get_user_model().DoesNotExist:
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
