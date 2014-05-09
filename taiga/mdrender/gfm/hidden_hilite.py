# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from markdown.extensions.codehilite import CodeHiliteExtension

class HiddenHiliteExtension(CodeHiliteExtension):
    """A subclass of CodeHiliteExtension that doesn't highlight on its own.

    This just enables the fenced code extension to use syntax highlighting,
    without adding syntax highlighting or line numbers to any additional code
    blocks.
    """

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
