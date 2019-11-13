# Copyright (C) 2014-2019 Taiga Agile LLC <taiga@taiga.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import re
from urllib.parse import parse_qs, urldefrag

import markdown
from markdown.treeprocessors import Treeprocessor

from taiga.projects.attachments.services import (get_attachment_by_id,
                                                 url_is_an_attachment)

REFRESH_PARAM = "_taiga-refresh"


def extract_refresh_id(url):
    if not url:
        return False, False
    _, frag = urldefrag(url)
    if not frag:
        return False, False
    qs = parse_qs(frag)
    if not qs:
        return False, False
    ref = qs.get(REFRESH_PARAM, False)
    if not ref:
        return False, False
    type_, _, id_ = ref[0].partition(":")
    try:
        return type_, int(id_)
    except ValueError:
        return False, False


def generate_refresh_fragment(attachment, type_=""):
    if not attachment:
        return ''
    return "{}={}:{}".format(REFRESH_PARAM, type_, attachment.id)


class RefreshAttachmentExtension(markdown.Extension):
    """An extension that refresh attachment URL."""
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        md.treeprocessors.add("refresh_attachment",
                              RefreshAttachmentTreeprocessor(md, project=self.project),
                              "<prettify")


class RefreshAttachmentTreeprocessor(Treeprocessor):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

    def run(self, root):
        # Bypass if not project
        if not self.project:
            return

        for tag, attr in [("img", "src"), ("a", "href")]:
            for el in root.iter(tag):
                url = url_is_an_attachment(el.get(attr, ""))
                if not url:
                    # It's not an attachment
                    break

                type_, attachment_id = extract_refresh_id(url)
                if not attachment_id:
                    # There is no refresh parameter
                    break

                attachment = get_attachment_by_id(self.project.id, attachment_id)
                if not attachment:
                    # Attachment not found or not permissions
                    break

                # Substitute url
                frag = generate_refresh_fragment(attachment, type_)
                new_url = "{}#{}".format(attachment.attached_file.url, frag)
                el.set(attr, new_url)
