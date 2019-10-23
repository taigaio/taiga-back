from unittest import mock

import pytest

from taiga.mdrender.extensions import refresh_attachment


@pytest.mark.parametrize("url, expected", [
    ("http://static.test/a/file.png", (False, False)),
    ("http://static.test/a/file.png?token=x", (False, False)),
    ("http://static.test/a/file.png?token=x#spurious", (False, False)),
    ("http://static.test/a/file.png?token=x#" + refresh_attachment.REFRESH_PARAM, (False, False)),
    ("http://static.test/a/file.png?token=x#" + refresh_attachment.REFRESH_PARAM + "=xxx", (False, False)),
    ("http://static.test/a/file.png?token=x#" + refresh_attachment.REFRESH_PARAM + "=us:42", ("us", 42)),
])
def test_render_attachment_extract_refresh_id(url, expected):
    assert refresh_attachment.extract_refresh_id(url) == expected


@pytest.mark.parametrize("attachment, expected", [
    (mock.MagicMock(id=42), refresh_attachment.REFRESH_PARAM + "=us:42"),
])
def test_render_attachment_generate_refresh_fragment(attachment, expected):
    assert refresh_attachment.generate_refresh_fragment(attachment, "us") == expected
