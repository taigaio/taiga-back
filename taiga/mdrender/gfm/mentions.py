#-*- coding: utf-8 -*-

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


import re
import os

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


class MentionsExtension(Extension):

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add('emojify',
                             MentionsPreprocessor(md),
                             '_end')


class MentionsPreprocessor(Preprocessor):

    def run(self, lines):
        new_lines = []
        pattern = re.compile('(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)')

        def make_mention_link(m):
            name = m.group(1)

            if not User.objects.filter(username=name):
                return "@{name}".format(name=name)

            tpl = ('[@{name}](/#/profile/{name} "@{name}")')
            return tpl.format(name=name)

        for line in lines:
            if line.strip():
                line = pattern.sub(make_mention_link, line)

            new_lines.append(line)

        return new_lines


def makeExtension(configs=None):
    return MentionsExtension(configs=configs)
