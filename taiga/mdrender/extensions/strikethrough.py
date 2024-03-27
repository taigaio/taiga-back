# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

# Copyright (c) 2013, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import markdown

STRIKE_RE = r'(~{2})(.+?)(~{2})'  # ~~strike~~


class StrikethroughExtension(markdown.Extension):
    """An extension that supports PHP-Markdown style strikethrough.

    For example: ``~~strike~~``.
    """

    def extendMarkdown(self, md):
        pattern = markdown.inlinepatterns.SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.register(pattern, 'strikethrough', 70)
