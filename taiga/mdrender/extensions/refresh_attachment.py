# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

#
import markdown
from markdown.treeprocessors import Treeprocessor

from taiga.projects.attachments.services import (
    extract_refresh_id, get_attachment_by_id, generate_refresh_fragment, url_is_an_attachment
)


class RefreshAttachmentExtension(markdown.Extension):
    """An extension that refresh attachment URL."""
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md):
        md.treeprocessors.register(RefreshAttachmentTreeprocessor(md, project=self.project),
                                   "refresh_attachment",
                                   20)


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
