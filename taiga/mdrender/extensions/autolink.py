# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import markdown
from markdown import inlinepatterns
from markdown.util import AtomicString
from xml.etree import ElementTree as etree

# We can't re-use the built-in AutolinkPattern because we need to add protocols
# to links without them.
class AutolinkPattern(inlinepatterns.Pattern):
    def handleMatch(self, m):
        el = etree.Element("a")

        href = m.group(2)
        if not re.match('^(ftp|https?)://', href, flags=re.IGNORECASE):
            href = 'http://%s' % href
        el.set('href', self.unescape(href))

        el.text = AtomicString(m.group(2))
        return el


class AutolinkExtension(markdown.Extension):
    """An extension that turns all URLs into links."""
    def extendMarkdown(self, md):
        url_re = '(%s)' % '|'.join([
            r'<(?:([Ff][Tt][Pp])|([Hh][Tt])[Tt][Pp][Ss]?)://[^>]*>',
            r'\b(?:([Ff][Tt][Pp])|([Hh][Tt])[Tt][Pp][Ss]?)://[^)<>\s]+[^.,)<>\s]',
            r'\bwww\.[^)<>\s]+[^.,)<>\s]',
        ])
        autolink = AutolinkPattern(url_re, md)
        md.inlinePatterns.register(autolink, 'autolink', 70)
