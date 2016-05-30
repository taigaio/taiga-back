# -*- coding: utf-8 -*-
# Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import markdown

STRIKE_RE = r'(~{2})(.+?)(~{2})'  # ~~strike~~


class StrikethroughExtension(markdown.Extension):
    """An extension that supports PHP-Markdown style strikethrough.

    For example: ``~~strike~~``.
    """

    def extendMarkdown(self, md, md_globals):
        pattern = markdown.inlinepatterns.SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.add('gfm-strikethrough', pattern, '_end')
