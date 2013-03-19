# -*- coding: utf-8 -*-

import sys
import codecs

from docutils import nodes
from docutils.parsers.rst import Directive, directives


def set_source_info(directive, node):
    node.source, node.line = \
        directive.state_machine.get_source_and_line(directive.lineno)


class CodeBlock(Directive):
    """
    Directive for a code block with special highlighting or line numbering
    settings.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        code = u'\n'.join(self.content)

        literal = nodes.literal_block(code, code)
        literal['classes'] = ['brush: java;']

        set_source_info(self, literal)
        return [literal]
