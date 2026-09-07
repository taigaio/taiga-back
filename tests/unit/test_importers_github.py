# -*- coding: utf-8 -*-

from unittest import mock

import pytest

from taiga.importers.github.importer import (
    GithubClient,
    extract_github_inline_image_urls,
)


def test_extract_github_inline_image_urls():
    attachment_url = "https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111"
    markdown = "![image]({}) ![same]({})".format(attachment_url, attachment_url)

    assert extract_github_inline_image_urls(markdown) == [attachment_url]


@pytest.mark.parametrize("markdown", [
    "![image](https://example.com/image.png)",
    "[issue](https://github.com/org/repo/issues/1)",
    "<img src=\"https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111\">",
    "![image](https://github.com/user-attachments/assets/not-a-uuid)",
])
def test_extract_github_inline_image_urls_ignores_unsupported_markdown(markdown):
    assert extract_github_inline_image_urls(markdown) == []


@mock.patch("taiga.importers.github.importer.requests.post")
def test_render_markdown_sends_context_and_authorization(post):
    post.return_value = mock.Mock(status_code=200, text="<img src=\"signed-url\">")
    client = GithubClient("oauth-token")

    rendered = client.render_markdown(
        "![image](https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111)",
        "owner/repository",
    )

    assert rendered == "<img src=\"signed-url\">"
    post.assert_called_once_with(
        "https://api.github.com/markdown",
        json={
            "text": "![image](https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111)",
            "mode": "gfm",
            "context": "owner/repository",
        },
        headers={
            "Accept": "text/html",
            "Content-Type": "application/json",
            "X-GitHub-Media-Type": "github.v3",
            "Authorization": "token oauth-token",
        },
    )


@mock.patch("taiga.importers.github.importer.requests.get")
def test_download_does_not_send_github_token(get):
    get.return_value = mock.Mock(
        status_code=200,
        content=b"image-bytes",
        headers={"Content-Type": "image/png"},
    )
    client = GithubClient("oauth-token")

    content, headers = client.download("https://private-user-images.githubusercontent.com/signed")

    assert content == b"image-bytes"
    assert headers["Content-Type"] == "image/png"
    get.assert_called_once_with("https://private-user-images.githubusercontent.com/signed")


@pytest.mark.parametrize("method", ["render_markdown", "download"])
def test_github_client_raises_for_unavailable_resource(method):
    with mock.patch("taiga.importers.github.importer.requests.post") as post, \
            mock.patch("taiga.importers.github.importer.requests.get") as get:
        post.return_value = mock.Mock(status_code=500, text="error")
        get.return_value = mock.Mock(status_code=404, text="error")
        client = GithubClient("oauth-token")

        with pytest.raises(Exception):
            if method == "render_markdown":
                client.render_markdown("![image](url)", "owner/repository")
            else:
                client.download("https://private-user-images.githubusercontent.com/signed")
