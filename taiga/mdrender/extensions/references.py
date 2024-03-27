# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC


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
from xml.etree import ElementTree as etree

from taiga.projects.references.services import get_instance_by_ref
from taiga.front.templatetags.functions import resolve


class TaigaReferencesExtension(Extension):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        return super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        TAIGA_REFERENCE_RE = r'(?<=^|(?<=[^a-zA-Z0-9-\[]))#(\d+)'
        referencesPattern = TaigaReferencesPattern(TAIGA_REFERENCE_RE, self.project)
        referencesPattern.md = md
        md.inlinePatterns.register(referencesPattern, 'taiga-references', 65)


class TaigaReferencesPattern(Pattern):
    def __init__(self, pattern, project):
        self.project = project
        super().__init__(pattern)

    def handleMatch(self, m):
        obj_ref = m.group(2)

        instance = get_instance_by_ref(self.project.id, obj_ref)
        if instance is None or instance.content_object is None:
            return "#{}".format(obj_ref)

        subject = instance.content_object.subject

        if instance.content_type.model == "epic":
            html_classes = "reference epic"
        elif instance.content_type.model == "userstory":
            html_classes = "reference user-story"
        elif instance.content_type.model == "task":
            html_classes = "reference task"
        elif instance.content_type.model == "issue":
            html_classes = "reference issue"
        else:
            return "#{}".format(obj_ref)

        url = resolve(instance.content_type.model, self.project.slug, obj_ref)

        link_text = "&num;{}".format(obj_ref)

        a = etree.Element('a')
        a.text = link_text
        a.set('href', url)
        a.set('title', "#{} {}".format(obj_ref, subject))
        a.set('class', html_classes)

        self.md.extracted_data['references'].append(instance.content_object)

        return a
