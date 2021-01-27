# -*- coding: utf-8 -*-
# Copyright (C) 2014-present Taiga Agile LLC
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

from unittest import mock

import pytest

from taiga.projects.attachments import services

from .. import factories as f


@pytest.mark.django_db(transaction=True)
def test_get_attachment_by_id(django_assert_num_queries):
    att, other_att = f.IssueAttachmentFactory(), f.IssueAttachmentFactory()
    assert att.content_object.project_id != other_att.content_object.project_id

    # Attachment not exist
    with django_assert_num_queries(1):
        assert services.get_attachment_by_id(other_att.content_object.project_id, 99999) is None

    # Attachment does not belong to an object of the project
    with django_assert_num_queries(2):
        assert services.get_attachment_by_id(other_att.content_object.project_id, att.id) is None

    # Attachment do belongs to the project
    with django_assert_num_queries(2):
        assert services.get_attachment_by_id(att.content_object.project_id, att.id) == att


@pytest.mark.parametrize("url, expected", [
    ("http://media.example.com/a/file.png", "http://media.example.com/a/file.png"),
    ("http://media.example.com/a/file.png?token=x", "http://media.example.com/a/file.png?token=x"),
    ("/a/file.png", None),
    ("http://www.example.com/logo.png", None),
])
def test_url_is_an_attachment(url, expected):
    assert services.url_is_an_attachment(url, base="http://media.example.com/a/") == expected


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("attachment_factory, expected", [
    (f.WikiAttachmentFactory, "wikipage"),
    (f.IssueAttachmentFactory, "issue"),
])
def test_generate_refresh_fragment(attachment_factory, expected):
    att = attachment_factory()
    frag = services.generate_refresh_fragment(att)
    assert "{}={}:{}".format(services.REFRESH_PARAM, expected, att.id) == frag


@pytest.mark.parametrize("url, expected", [
    ("http://static.test/a/file.png", (False, False)),
    ("http://static.test/a/file.png?token=x", (False, False)),
    ("http://static.test/a/file.png?token=x#spurious", (False, False)),
    ("http://static.test/a/file.png?token=x#" + services.REFRESH_PARAM, (False, False)),
    ("http://static.test/a/file.png?token=x#" + services.REFRESH_PARAM + "=xxx", (False, False)),
    ("http://static.test/a/file.png?token=x#" + services.REFRESH_PARAM + "=us:42", ("us", 42)),
])
def test_render_attachment_extract_refresh_id(url, expected):
    assert services.extract_refresh_id(url) == expected


@pytest.mark.parametrize("attachment, expected", [
    (mock.MagicMock(id=42), services.REFRESH_PARAM + "=us:42"),
])
def test_generate_refresh_fragment_with_type(attachment, expected):
    assert services.generate_refresh_fragment(attachment, "us") == expected
