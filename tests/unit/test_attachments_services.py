# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

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
