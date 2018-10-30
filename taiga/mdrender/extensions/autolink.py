# -*- coding: utf-8 -*-
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import re
import markdown


# We can't re-use the built-in AutolinkPattern because we need to add protocols
# to links without them.
class AutolinkPattern(markdown.inlinepatterns.Pattern):
    def handleMatch(self, m):
        el = markdown.util.etree.Element("a")

        href = m.group(2)
        if not re.match('^(ftp|https?)://', href, flags=re.IGNORECASE):
            href = 'http://%s' % href
        el.set('href', self.unescape(href))

        el.text = markdown.util.AtomicString(m.group(2))
        return el


class AutolinkExtension(markdown.Extension):
    """An extension that turns all URLs into links.

    This is based on the web-only URL regex by John Gruber that's listed on
    http://daringfireball.net/2010/07/improved_regex_for_matching_urls (which is
    in the public domain).

    This regex seems to line up pretty closely with GitHub's URL matching. There
    are only two cases I've found where they differ. In both cases, I've
    modified the regex slightly to bring it in line with GitHub's parsing:

    * GitHub accepts FTP-protocol URLs.
    * GitHub only accepts URLs with protocols or "www.", whereas Gruber's regex
      accepts things like "foo.com/bar".
    """
    def extendMarkdown(self, md):
        url_re = r'(?i)\b((?:(?:ftp|https?)://|www\d{0,3}[.])([^\s<>]+))'
        autolink = AutolinkPattern(url_re, md)
        md.inlinePatterns.add('gfm-autolink', autolink, '_end')
